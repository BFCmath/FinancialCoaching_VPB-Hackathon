reading: [text](for_ai.md)
reading: [text](detail_context.md)

> reading all files I sent
> Always reading to confirm instead of asssuming wrong context
> avoid hallucination efffectively by reading lines by lines and take note as you go

# transaction_classifier
+ this classify the transaction into jars
+ input seem to match: a message about what user spend on one time (like meal, gas, etc.)

# fee_manager
+ this will handle the fee tracking and management (fee mean recurring fee, like subscription, daily commute, etc.)
+ input seem to match: a message about a repetitive fee, like "1 dollar every monday and friday for commute", "10 dollar every month for youtube subscription", ...

# jar_manager
+ this will handle jar creation and modification (thinking like CRUD natural language command)
+ for example: "I want to add a new jar for my vacation to Korea", or "Reduce the Save jar percent to 2%"
+ input seem to match: a message about what user want to do with jar, sometime they dont explicit mention the jar name

# budget_advisor
+ this will handle the budget planning and financial advice
+ input seem to match: a message about what user want to do with budget, like "I want to save money for my parents, can you propose some plan"

# insight_generator
+ this will help the user understand more about their spending and financial situation
+ input seem to match: a message about what user want to know about their spending and financial situation, like "I want to know my spending trend", or "Will I have enough time to save for the trip to thai lan?"

# alerting_coach
+ this is not a tool for orchestrator, it is a tool for alert system
+ when an event trigger (likely user overspend on a jar), it will send a message to the user (with deep analysis based on insight generator)
