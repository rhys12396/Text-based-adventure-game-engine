# Text-based-adventure-game-engine
A small, data-driven text adventure engine in Python. The engine knows nothing about any particular story. You describe rooms, exits and items in a JSON file, and the engine loads it, validates it and runs the game loop.

FEATURES

	Stories defined entirely in JSON, no engine code changes needed
	Startup validation with clear, collected error messages
	Rooms, exits and takeable items
	Locked exits that require an item in your inventory
	Verb and noun parser with aliases and shortcuts (n, i, grab, etc.)
	Game state kept separate from story data, which makes save/load easy to add
	No dependencies beyond the Python standard library


REQUIREMENTS

	Python 3.8 or newer


QUICK START

	1. Save the engine as engine.py
	2. Save a story file as cellar_story.json in the same folder (a complete example is below)
	3. Run:

		python engine.py

	To play a different story, change the path in the last line of engine.py:

		if __name__ == "__main__":
			run(load_story("your_story.json"))


PLAYING

Type commands at the > prompt.

	look				Describe the current room (alias: l)
	go <direction>			Move through an exit (aliases: walk, move)
	north, south, east,
	west, up, down			Shortcut for go <direction> (aliases: n, s, e, w, u, d)
	take <item>			Pick up an item in the room (aliases: grab, get)
	drop <item>			Drop an item you are carrying
	inventory			List what you are carrying (aliases: i, inv)
	quit				Exit the game

Items can be referred to by id, full name, or any single word of the name. So "take brass lantern", "take lantern" and "take brass" all work.


STORY FILE FORMAT

A story is a JSON object with three top-level keys:

	start		Required. Id of the room where the player begins
	rooms		Required. Map of room id to room definition
	items		Optional. Map of item id to item definition

Rooms

	description	Required. Text shown when the player enters or looks
	exits		Optional. Map of direction to exit (see below)
	items		Optional. List of item ids that start in this room

Exits

An exit is either a plain room id, or an object with a locking requirement.

	"north": "hallway"

	"east": { "to": "vault", "requires": "brass_key" }

A locked exit blocks the player unless the required item is in their inventory.

Items

	name		Required. Display name shown to the player
	takeable	Optional. Whether the player can pick it up (default false)

Complete example: cellar_story.json

	{
		"start": "cellar",
		"rooms": {
			"cellar": {
				"description": "A damp cellar. Stairs lead up to the north.",
				"exits": { "north": "hallway" },
				"items": ["lantern"]
			},
			"hallway": {
				"description": "A dusty hallway. A locked door stands to the east.",
				"exits": {
					"south": "cellar",
					"east": { "to": "vault", "requires": "brass_key" },
					"west": "study"
				}
			},
			"study": {
				"description": "A cramped study smelling of old paper.",
				"exits": { "east": "hallway" },
				"items": ["brass_key"]
			},
			"vault": {
				"description": "A small vault. Something glitters in the corner. You win!",
				"exits": { "west": "hallway" }
			}
		},
		"items": {
			"lantern": { "name": "brass lantern", "takeable": true },
			"brass_key": { "name": "brass key", "takeable": true }
		}
	}

A winning playthrough: take lantern, n, w, take key, e, e


VALIDATION

When a story loads, validate() checks it and reports every problem at once instead of stopping at the first. It catches:

	Missing start or rooms keys
	A start room that does not exist
	Rooms with no description
	Exits that lead to unknown rooms
	Locked exits that require an unknown item
	Rooms that contain unknown items

Example output:

	ValueError: Story has errors:
	Room 'hallway': exit 'east' leads to unknown room 'vualt'

Validation checks structure only. It does not check that the story is winnable.


HOW IT WORKS

	JSON file -> load_story() -> story (static data)
	new_state() -> state (changes during play)
	run(): input -> handle_command() -> handler -> text -> print

Main pieces:

	load_story(path)			Parses the JSON file and validates it
	validate(story)				Raises ValueError listing all story errors
	new_state(story)			Builds the starting state: current room, inventory, flags, item locations
	describe_room(story, state)		Builds the text for the current room
	handle_command(story, state, raw)	Normalizes input, applies aliases, dispatches to a handler
	HANDLERS				Table mapping each verb to its do_* function
	run(story)				The main loop: read input, handle it, print the result

Design points:

	Story data never changes during play. Anything that changes (current room, inventory, where items are) lives in state. Item locations are copied into state["room_items"] at startup so take and drop never modify the story.

	Every handler has the same signature, (story, state, noun), and returns a string. That keeps them testable and lets a different front end (web, chat bot) reuse the engine by calling handle_command and displaying the result.


EXTENDING THE ENGINE

Add a verb: write a function with the handler signature, then register it.

	def do_examine(story, state, noun):
		return "You see nothing special."

	HANDLERS["examine"] = do_examine
	ALIASES["x"] = "examine"

Add an alias: add an entry to ALIASES.

Add a story feature: add the field to the JSON, teach validate() about it, and read it in the relevant handler. Avoid hardcoding story-specific logic such as if room == "vault" in the engine.


KNOWN LIMITATIONS

	No win condition. Reaching the vault prints its description, but the game keeps running.
	Keys are not consumed. A locked exit only checks that the item is in your inventory, so unlocking is not permanent.
	The flags dictionary exists but is not used yet.
	Two-part commands are not supported. The parser handles verb and noun only, so "unlock door with key" is not understood.
	No save/load.
	Dark rooms, NPCs and timed events are not implemented.


ROADMAP

	1. use X on Y with a second noun slot
	2. Flags, so unlocking an exit is permanent
	3. Conditional descriptions and exits based on flags
	4. Win and lose conditions that end the game
	5. Save/load by serializing state to JSON
	6. First-visit vs. return-visit room descriptions
	7. NPCs and simple dialogue


TROUBLESHOOTING

	FileNotFoundError		The story file is not in the folder you are running from
	json.JSONDecodeError		Syntax error in the JSON, such as a missing comma. The message gives the line
	ValueError: Story has errors	The story failed validation. Each problem is listed
	I don't see a X here.		The item is not in the room, or you mistyped its name
