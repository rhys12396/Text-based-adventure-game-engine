import json

def validate(story):
    errors = []

    for key in ("start", "rooms"):
        if key not in story:
            errors.append(f"Missing required key: '{key}'")

    if errors:
        raise ValueError("\n".join(errors))

    rooms = story["rooms"]
    items = story.get("items", {})

    if story["start"] not in rooms:
        errors.append(f"Start room '{story['start']}' does not exist")

    for room_id, room in rooms.items():
        if "description" not in room:
            errors.append(f"Room '{room_id}' has no description")

        for direction, exit_ in room.get("exits", {}).items():
            target = exit_ if isinstance(exit_, str) else exit_.get("to")
            if target not in rooms:
                errors.append(f"Room '{room_id}': exit '{direction}' leads to unknown room '{target}'")

            if isinstance(exit_, dict) and "requires" in exit_:
                if exit_["requires"] not in items:
                    errors.append(f"Room '{room_id}': exit '{direction}' requires unknown item '{exit_['requires']}'")

        for item_id in room.get("items", []):
            if item_id not in items:
                errors.append(f"Room '{room_id}' contains unknown item '{item_id}'")

    if errors:
        raise ValueError("Story has errors:\n" + "\n".join(errors)) 

DIRECTIONS = {"north", "south", "east", "west", "up", "down"}

ALIASES = {
    "n": "north", "s": "south", "e": "east", "w": "west", "u": "up", "d": "down",
    "i": "inventory", "inv": "inventory", "l": "look",
    "grab": "take", "get": "take", "walk": "go", "move": "go"
}

def find_item(story, item_ids, noun):
    """Match 'lantern' or 'brass lantern' or the item id against a list of item ids."""
    for item_id in item_ids:
        name = story["items"][item_id]["name"]
        if noun == item_id or noun == name or noun in name.split():
            return item_id
    return None

def do_look(story, state, noun):
    return describe_room(story, state)

def do_inventory(story, state, noun):
    if not state["inventory"]:
        return "You're carrying nothing."
    names = [story["items"][i]["name"] for i in state["inventory"]]
    return "You're carrying: " + ", ".join(names) + "."

def do_go(story, state, noun):
    if not noun:
        return "Go where?"
    room = story["rooms"][state["room"]]
    exit_ = room.get("exits", {}).get(noun)
    if exit_ is None:
        return "You can't go that way."

    if isinstance(exit_, str):
        target = exit_
    else:
        target = exit_["to"]
        needed = exit_.get("requires")
        if needed and needed not in state["inventory"]:
            return "The way is locked."

    state["room"] = target
    return describe_room(story, state)

def do_take(story, state, noun):
    if not noun:
        return "Take what?"
    here = state["room_items"][state["room"]]
    item_id = find_item(story, here, noun)
    if item_id is None:
        return f"I don't see a {noun} here."
    if not story["items"][item_id].get("takeable", False):
        return "You can't take that."
    here.remove(item_id)
    state["inventory"].append(item_id)
    return f"Taken: {story['items'][item_id]['name']}."

def do_drop(story, state, noun):
    if not noun:
        return "Drop what?"
    item_id = find_item(story, state["inventory"], noun)
    if item_id is None:
        return f"You aren't carrying a {noun}."
    state["inventory"].remove(item_id)
    state["room_items"][state["room"]].append(item_id)
    return f"Dropped: {story['items'][item_id]['name']}."

def do_quit(story, state, noun):
    raise SystemExit("Thanks for playing.")

HANDLERS = {
    "look": do_look,
    "inventory": do_inventory,
    "go": do_go,
    "take": do_take,
    "drop": do_drop,
    "quit": do_quit,
}

def handle_command(story, state, raw):
    words = raw.lower().split()
    if not words:
        return "Say something."

    verb = ALIASES.get(words[0], words[0])
    noun = " ".join(ALIASES.get(w, w) if i == 0 else w
                    for i, w in enumerate(words[1:]))

    # bare direction ("north", "n") means "go north"
    if verb in DIRECTIONS:
        verb, noun = "go", verb

    handler = HANDLERS.get(verb)
    if handler is None:
        return f"I don't know how to '{verb}'."
    return handler(story, state, noun)

def describe_room(story, state):
    room = story["rooms"][state["room"]]
    lines = [room["description"]]

    visible = [story["items"][i]["name"] for i in state["room_items"][state["room"]]]
    if visible:
        lines.append("You see: " + ", ".join(visible) + ".")

    if room.get("exits"):
        lines.append("Exits: " + ", ".join(room["exits"].keys()) + ".")

    return "\n".join(lines)

def load_story(path):
    with open(path) as f:
        story = json.load(f)
    validate(story)
    return story

def new_state(story):
    return {
        "room": story["start"], 
        "inventory": [], 
        "flags": {},
        "room_items": {rid: list(r.get("items", [])) for rid, r in story["rooms"].items()},
        }

def run(story):
    state = new_state(story)
    print(describe_room(story, state))
    while True:
        command = input("> ")
        output = handle_command(story, state, command)
        print(output)

if __name__ == "__main__":
    run(load_story("cellar_story.json"))