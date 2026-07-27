from datetime import datetime, timezone
from bson import ObjectId
from db import get_journals_collection
from utils.serializers import serialize_doc
from utils.jwt_helper import extract_token_from_header, decode_token

def _build_user_id_query(user_id_str):
    """
    Builds a flexible user_id query supporting both string and ObjectId formats.
    """
    if ObjectId.is_valid(user_id_str):
        return {"$in": [user_id_str, ObjectId(user_id_str)]}
    return user_id_str

def _sanitize_tags(tags):
    """
    Cleans tags array to ensure a list of non-empty strings.
    """
    if not isinstance(tags, list):
        return []
    sanitized = []
    for tag in tags:
        if isinstance(tag, (str, int, float)):
            s_tag = str(tag).strip()
            if s_tag and s_tag not in sanitized:
                sanitized.append(s_tag)
    return sanitized

def _extract_user_id_from_auth_header(auth_header):
    """
    Safely attempts to extract user_id from an Authorization header without raising errors.
    """
    token = extract_token_from_header(auth_header)
    if not token:
        return None
    payload, error = decode_token(token)
    if error or not payload:
        return None
    return payload.get("user_id")

def _enrich_post_reactions(post_doc, current_user_id=None):
    """
    Attaches computed reaction_counts, total_reactions, and current user_reaction to post_doc dictionary.
    """
    if not post_doc or not isinstance(post_doc, dict):
        return post_doc

    reactions = post_doc.get("reactions", [])
    if not isinstance(reactions, list):
        reactions = []

    # Calculate reaction counts map
    counts = {}
    user_reaction = None
    curr_user_str = str(current_user_id) if current_user_id else None

    for r in reactions:
        if not isinstance(r, dict):
            continue
        r_type = r.get("type", "like")
        counts[r_type] = counts.get(r_type, 0) + 1
        if curr_user_str and str(r.get("user_id")) == curr_user_str:
            user_reaction = r_type

    post_doc["reaction_counts"] = counts
    post_doc["total_reactions"] = sum(counts.values())
    post_doc["user_reaction"] = user_reaction
    return post_doc

def fetch_public_feed(limit=20, skip=0, auth_header=None):
    """
    Fetches public community feed sorted by creation date (newest first).
    """
    safe_limit = max(1, min(int(limit), 100))
    safe_skip = max(0, int(skip))

    requester_user_id = _extract_user_id_from_auth_header(auth_header)

    journals = get_journals_collection()
    cursor = journals.find({"is_public": True}).sort("created_at", -1).skip(safe_skip).limit(safe_limit)
    posts = [_enrich_post_reactions(serialize_doc(post), requester_user_id) for post in cursor]
    total = journals.count_documents({"is_public": True})

    return {
        "posts": posts,
        "total": total,
        "limit": safe_limit,
        "skip": safe_skip
    }, None, 200

def create_journal_entry(user_id, author_username, title, content, tags=None, is_public=False):
    """
    Creates a new journal post (Public or Private).
    """
    now = datetime.now(timezone.utc)
    post_doc = {
        "user_id": str(user_id),
        "author_username": str(author_username or "Anonymous").strip(),
        "title": str(title).strip(),
        "content": str(content).strip(),
        "tags": _sanitize_tags(tags),
        "is_public": bool(is_public),
        "reactions": [],
        "reaction_counts": {},
        "created_at": now,
        "updated_at": now
    }

    journals = get_journals_collection()
    result = journals.insert_one(post_doc)
    post_doc["_id"] = result.inserted_id

    serialized = serialize_doc(post_doc)
    enriched = _enrich_post_reactions(serialized, user_id)

    return {
        "message": "Journal created successfully",
        "post": enriched
    }, None, 201

def fetch_user_journals(user_id, is_public_filter=None):
    """
    Fetches journals belonging to a specific user.
    Optionally filters by is_public boolean flag.
    """
    query = {"user_id": _build_user_id_query(user_id)}
    if is_public_filter is not None:
        query["is_public"] = bool(is_public_filter)

    journals = get_journals_collection()
    cursor = journals.find(query).sort("created_at", -1)
    posts = [_enrich_post_reactions(serialize_doc(post), user_id) for post in cursor]

    return {
        "posts": posts,
        "count": len(posts)
    }, None, 200

def get_journal_detail(post_id, auth_header=None):
    """
    Fetches single journal detail with privacy authorization check.
    """
    journals = get_journals_collection()
    post = journals.find_one({"_id": ObjectId(post_id)})

    if not post:
        return None, "Journal post not found!", 404

    requester_user_id = _extract_user_id_from_auth_header(auth_header)

    # Check privacy permissions for private posts
    if not post.get("is_public", False):
        if not requester_user_id:
            return None, "This post is private. Authentication is required to view it.", 403

        if str(requester_user_id) != str(post["user_id"]):
            return None, "You do not have permission to view this private journal.", 403

    serialized = serialize_doc(post)
    enriched = _enrich_post_reactions(serialized, requester_user_id)

    return {"post": enriched}, None, 200

def update_journal_privacy(post_id, user_id, is_public):
    """
    Updates the privacy status (is_public: True/False) of an existing post.
    """
    journals = get_journals_collection()
    post = journals.find_one({"_id": ObjectId(post_id)})

    if not post:
        return None, "Journal post not found!", 404

    if str(post["user_id"]) != str(user_id):
        return None, "You can only modify privacy settings for your own posts!", 403

    now = datetime.now(timezone.utc)
    journals.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"is_public": bool(is_public), "updated_at": now}}
    )

    updated_post = journals.find_one({"_id": ObjectId(post_id)})
    status_str = "public" if is_public else "private"

    return {
        "message": f"Journal privacy successfully updated to {status_str}.",
        "post": _enrich_post_reactions(serialize_doc(updated_post), user_id)
    }, None, 200

def update_journal_entry(post_id, user_id, data):
    """
    Updates post title, content, tags, or privacy settings (Author only).
    """
    journals = get_journals_collection()
    post = journals.find_one({"_id": ObjectId(post_id)})

    if not post:
        return None, "Journal post not found!", 404

    if str(post["user_id"]) != str(user_id):
        return None, "You can only edit your own posts!", 403

    update_fields = {"updated_at": datetime.now(timezone.utc)}

    if "title" in data:
        new_title = str(data["title"]).strip()
        if not new_title:
            return None, "Journal title cannot be empty!", 400
        if len(new_title) > 300:
            return None, "Journal title cannot exceed 300 characters!", 400
        update_fields["title"] = new_title

    if "content" in data:
        new_content = str(data["content"]).strip()
        if not new_content:
            return None, "Journal content cannot be empty!", 400
        if len(new_content) > 100000:
            return None, "Journal content cannot exceed 100,000 characters!", 400
        update_fields["content"] = new_content

    if "tags" in data:
        update_fields["tags"] = _sanitize_tags(data["tags"])

    if "is_public" in data:
        update_fields["is_public"] = bool(data["is_public"])

    journals.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": update_fields}
    )

    updated_post = journals.find_one({"_id": ObjectId(post_id)})

    return {
        "message": "Journal updated successfully",
        "post": _enrich_post_reactions(serialize_doc(updated_post), user_id)
    }, None, 200

def delete_journal_entry(post_id, user_id):
    """
    Deletes a journal entry (Author only).
    """
    journals = get_journals_collection()
    post = journals.find_one({"_id": ObjectId(post_id)})

    if not post:
        return None, "Journal post not found!", 404

    if str(post["user_id"]) != str(user_id):
        return None, "You can only delete your own posts!", 403

    journals.delete_one({"_id": ObjectId(post_id)})

    return {
        "message": "Journal post deleted successfully."
    }, None, 200

def add_or_toggle_reaction(post_id, user_id, username, reaction_type="like"):
    """
    Adds, updates, or toggles off a reaction on a post.
    """
    journals = get_journals_collection()
    post = journals.find_one({"_id": ObjectId(post_id)})

    if not post:
        return None, "Journal post not found!", 404

    # Permission check for private post
    if not post.get("is_public", False) and str(post.get("user_id")) != str(user_id):
        return None, "You do not have permission to react to this private journal.", 403

    reaction_type = str(reaction_type or "like").strip()
    if not reaction_type:
        reaction_type = "like"

    reactions = post.get("reactions", [])
    if not isinstance(reactions, list):
        reactions = []

    user_id_str = str(user_id)
    existing_idx = None
    existing_type = None

    for idx, r in enumerate(reactions):
        if isinstance(r, dict) and str(r.get("user_id")) == user_id_str:
            existing_idx = idx
            existing_type = r.get("type")
            break

    now = datetime.now(timezone.utc)
    if existing_idx is not None:
        if existing_type == reaction_type:
            # Toggle off: user clicked same reaction again
            reactions.pop(existing_idx)
            action = "removed"
            user_reaction = None
            msg = f"Reaction '{reaction_type}' removed."
        else:
            # Update reaction type
            reactions[existing_idx]["type"] = reaction_type
            reactions[existing_idx]["created_at"] = now
            action = "updated"
            user_reaction = reaction_type
            msg = f"Reaction updated to '{reaction_type}'."
    else:
        # Add new reaction
        reactions.append({
            "user_id": user_id_str,
            "username": str(username or "Anonymous").strip(),
            "type": reaction_type,
            "created_at": now
        })
        action = "added"
        user_reaction = reaction_type
        msg = f"Reaction '{reaction_type}' added."

    # Compute updated counts map
    counts = {}
    for r in reactions:
        if isinstance(r, dict):
            t = r.get("type", "like")
            counts[t] = counts.get(t, 0) + 1

    journals.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"reactions": reactions, "reaction_counts": counts, "updated_at": now}}
    )

    total_reactions = sum(counts.values())

    return {
        "message": msg,
        "data": {
            "post_id": str(post_id),
            "reaction_counts": counts,
            "total_reactions": total_reactions,
            "user_reaction": user_reaction,
            "action": action
        }
    }, None, 200

def remove_reaction(post_id, user_id):
    """
    Removes user's reaction from a post if present.
    """
    journals = get_journals_collection()
    post = journals.find_one({"_id": ObjectId(post_id)})

    if not post:
        return None, "Journal post not found!", 404

    if not post.get("is_public", False) and str(post.get("user_id")) != str(user_id):
        return None, "You do not have permission to modify reactions on this private journal.", 403

    reactions = post.get("reactions", [])
    if not isinstance(reactions, list):
        reactions = []

    user_id_str = str(user_id)
    new_reactions = [r for r in reactions if isinstance(r, dict) and str(r.get("user_id")) != user_id_str]

    counts = {}
    for r in new_reactions:
        t = r.get("type", "like")
        counts[t] = counts.get(t, 0) + 1

    now = datetime.now(timezone.utc)
    journals.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"reactions": new_reactions, "reaction_counts": counts, "updated_at": now}}
    )

    total_reactions = sum(counts.values())

    return {
        "message": "Reaction removed successfully.",
        "data": {
            "post_id": str(post_id),
            "reaction_counts": counts,
            "total_reactions": total_reactions,
            "user_reaction": None,
            "action": "removed"
        }
    }, None, 200

def get_post_reactions_detail(post_id, auth_header=None):
    """
    Fetches detailed reaction list and breakdown for a journal post.
    """
    journals = get_journals_collection()
    post = journals.find_one({"_id": ObjectId(post_id)})

    if not post:
        return None, "Journal post not found!", 404

    requester_user_id = _extract_user_id_from_auth_header(auth_header)

    if not post.get("is_public", False):
        if not requester_user_id:
            return None, "This post is private. Authentication is required to view reactions.", 403

        if str(requester_user_id) != str(post["user_id"]):
            return None, "You do not have permission to view reactions on this private journal.", 403

    serialized = serialize_doc(post)
    enriched = _enrich_post_reactions(serialized, requester_user_id)

    raw_reactions = serialized.get("reactions", [])
    reactions_list = []
    if isinstance(raw_reactions, list):
        for r in raw_reactions:
            if isinstance(r, dict):
                reactions_list.append({
                    "user_id": str(r.get("user_id", "")),
                    "username": str(r.get("username", "Anonymous")),
                    "type": str(r.get("type", "like")),
                    "created_at": r.get("created_at")
                })

    return {
        "data": {
            "post_id": str(post_id),
            "reactions": reactions_list,
            "reaction_counts": enriched["reaction_counts"],
            "total_reactions": enriched["total_reactions"],
            "user_reaction": enriched["user_reaction"]
        }
    }, None, 200

