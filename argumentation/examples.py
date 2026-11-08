"""Named fixtures; book example numbers require the actual textbook graphs."""

EXAMPLES = {
    "book-5.11": {
        "name": "Book · Example 5.11",
        "description": "Chapter 5, p. 201. a6 cancels indirect self-defeat. Truthfulness is dominant.",
        "arguments": ["a1", "a2", "a3", "a4", "a5", "a6"],
        "attacks": [["a1", "a2"], ["a2", "a3"], ["a3", "a4"], ["a3", "a5"], ["a6", "a3"]],
        "ownership": {"x": ["a1", "a4", "a5", "a6"], "y": ["a2"], "z": ["a3"]},
    },
    "book-5.10": {
        "name": "Book · Example 5.10",
        "description": "Chapter 5, pp. 199–200. Correct full-report utilities: x = 1, y = 0, z = 1.",
        "arguments": ["a1", "a2", "a3", "a4", "a5"],
        "attacks": [["a1", "a2"], ["a2", "a3"], ["a3", "a4"], ["a3", "a5"]],
        "ownership": {"x": ["a1", "a4", "a5"], "y": ["a2"], "z": ["a3"]},
    },
    "book-5.1": {
        "name": "Book · Figure 5.1 / Examples 5.5–5.6, 5.8",
        "description": "Chapter 5, pp. 181–184. {a3, a5} defends a1; grounded = {a1, a3, a5}.",
        "arguments": ["a1", "a2", "a3", "a4", "a5"],
        "attacks": [["a2", "a1"], ["a4", "a1"], ["a3", "a2"], ["a5", "a4"]],
        "ownership": {"x": ["a1"], "y": ["a2", "a3"], "z": ["a4", "a5"]},
    },
    "book-5.2": {
        "name": "Book · Figure 5.2 / Examples 5.7–5.8",
        "description": "Chapter 5, pp. 183–184. Three complete extensions and two preferred extensions.",
        "arguments": ["a1", "a2", "a3"],
        "attacks": [["a1", "a2"], ["a2", "a1"]],
        "ownership": {"x": ["a1"], "y": ["a2"], "z": ["a3"]},
    },
    "chain": {
        "name": "Defence chain",
        "description": "a defeats b; b defeats c. Grounded = {a, c}.",
        "arguments": ["a", "b", "c"],
        "attacks": [["a", "b"], ["b", "c"]],
        "ownership": {"Agent 1": ["a"], "Agent 2": ["b"], "Agent 3": ["c"]},
    },
    "mutual": {
        "name": "Mutual attack",
        "description": "Two preferred and stable extensions; grounded is empty.",
        "arguments": ["a", "b"],
        "attacks": [["a", "b"], ["b", "a"]],
        "ownership": {"Agent 1": ["a"], "Agent 2": ["b"], "Agent 3": []},
    },
    "odd-cycle": {
        "name": "Odd cycle",
        "description": "No stable extension. All arguments are undecided.",
        "arguments": ["a", "b", "c"],
        "attacks": [["a", "b"], ["b", "c"], ["c", "a"]],
        "ownership": {"Agent 1": ["a"], "Agent 2": ["b"], "Agent 3": ["c"]},
    },
    "hiding": {
        "name": "Profitable hiding",
        "description": "Rahwan & Larson (2008), Example 26. Agent 1 gains 1 → 2 by hiding a.",
        "arguments": ["a", "b", "c", "d", "e"],
        "attacks": [["a", "b"], ["b", "c"], ["c", "d"], ["c", "e"]],
        "ownership": {"Agent 1": ["a", "d", "e"], "Agent 2": ["b"], "Agent 3": ["c"]},
    },
    "harmless": {
        "name": "Condition fails, truthfulness holds",
        "description": "One agent owns a and b with a → b. Hiding a exchanges one accepted argument for another.",
        "arguments": ["a", "b", "c"],
        "attacks": [["a", "b"]],
        "ownership": {"Agent 1": ["a", "b"], "Agent 2": ["c"], "Agent 3": []},
    },
    "paper-defence": {
        "name": "Two-sided defence",
        "description": "Rahwan & Larson (2008), Figure 1: grounded = {a1, a3, a5}.",
        "arguments": ["a1", "a2", "a3", "a4", "a5"],
        "attacks": [["a2", "a1"], ["a4", "a1"], ["a3", "a2"], ["a5", "a4"]],
        "ownership": {"Agent 1": ["a1"], "Agent 2": ["a2", "a3"], "Agent 3": ["a4", "a5"]},
    },
}
