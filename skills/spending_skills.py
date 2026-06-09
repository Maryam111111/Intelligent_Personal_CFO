"""Skills for SpendingAgent."""

from skills.skill import Skill

CATEGORISE = Skill(
    name="categorise_transactions",
    description="Group transactions by category and compute totals.",
    prompt_template=(
        "Given these transactions (CSV):\n{transactions}\n\n"
        "Group by category and return total spent per category. "
        "Identify any transactions that appear miscategorised."
    ),
)

DETECT_ANOMALIES = Skill(
    name="detect_anomalies",
    description="Flag unusually large or out-of-pattern transactions.",
    prompt_template=(
        "Review these transactions:\n{transactions}\n\n"
        "Flag any that are unusually large, out-of-character, "
        "or suggest a one-off vs regular pattern."
    ),
)

RANK_CATEGORIES = Skill(
    name="rank_categories",
    description="Rank spending categories highest to lowest.",
    prompt_template=(
        "From this category breakdown:\n{category_breakdown}\n\n"
        "Rank categories from highest to lowest spend. "
        "Identify the top 3 and comment on whether each is proportionate."
    ),
)

FLAG_RECURRING = Skill(
    name="flag_recurring",
    description="Identify subscriptions and recurring costs.",
    prompt_template=(
        "Review these transactions:\n{transactions}\n\n"
        "List all apparent subscriptions or recurring charges "
        "(same merchant, regular interval). Include monthly total."
    ),
)
