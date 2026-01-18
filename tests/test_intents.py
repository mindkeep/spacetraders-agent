from agent.intents import Intent, IntentType


def test_intent_summary():
    intent = Intent(
        intent_type=IntentType.EXPLORE,
        goal="Scout nearby systems",
        reasoning="Placeholder",
        details={"system": "X1"},
    )
    assert intent.summary() == "explore: Scout nearby systems"
