"""
Study Planner — Algorithmic study schedule generation.

Generates weighted, day-by-day study plans based on:
- Topics from syllabus (via RAG)
- Days until exam
- Topic importance / exam weightage
"""

from datetime import datetime, timedelta
import math


def generate_study_plan(
    topics: list[dict],
    exam_date: str,
    hours_per_day: float = 2.5,
    buffer_days: int = 3,
) -> dict:
    """
    Generate a day-by-day study schedule.

    Args:
        topics: List of dicts with 'name' and optional 'weight' (1.0 = normal).
        exam_date: ISO date string (YYYY-MM-DD).
        hours_per_day: Available study hours per day.
        buffer_days: Days reserved for revision before the exam.

    Returns:
        Dictionary with schedule, stats, and recommendations.
    """
    today = datetime.now().date()
    exam = datetime.strptime(exam_date, "%Y-%m-%d").date()
    total_days = (exam - today).days

    if total_days <= 0:
        return {
            "error": "Exam date must be in the future.",
            "schedule": [],
            "stats": {},
        }

    study_days = max(total_days - buffer_days, 1)

    # Assign default weights if missing
    for topic in topics:
        topic.setdefault("weight", 1.0)

    total_weight = sum(t["weight"] for t in topics)

    # Distribute days across topics proportionally
    schedule = []
    current_date = today + timedelta(days=1)  # Start tomorrow

    for topic in topics:
        proportion = topic["weight"] / total_weight
        days_allocated = max(1, round(proportion * study_days))
        hours_total = days_allocated * hours_per_day

        topic_schedule = {
            "topic": topic["name"],
            "days_allocated": days_allocated,
            "total_hours": round(hours_total, 1),
            "hours_per_day": hours_per_day,
            "start_date": current_date.isoformat(),
            "end_date": (current_date + timedelta(days=days_allocated - 1)).isoformat(),
            "priority": _get_priority(topic["weight"]),
        }
        schedule.append(topic_schedule)
        current_date += timedelta(days=days_allocated)

    # Add revision period
    revision_start = exam - timedelta(days=buffer_days)
    schedule.append({
        "topic": "📝 Revision & Practice",
        "days_allocated": buffer_days,
        "total_hours": round(buffer_days * hours_per_day, 1),
        "hours_per_day": hours_per_day,
        "start_date": revision_start.isoformat(),
        "end_date": (exam - timedelta(days=1)).isoformat(),
        "priority": "🔴 Critical",
    })

    # Stats
    stats = {
        "total_topics": len(topics),
        "total_days": total_days,
        "study_days": study_days,
        "revision_days": buffer_days,
        "hours_per_day": hours_per_day,
        "total_study_hours": round(study_days * hours_per_day, 1),
        "exam_date": exam_date,
    }

    return {
        "schedule": schedule,
        "stats": stats,
        "recommendations": _generate_recommendations(topics, study_days),
    }


def _get_priority(weight: float) -> str:
    """Map weight to a human-readable priority label."""
    if weight >= 2.0:
        return "🔴 High Priority"
    elif weight >= 1.5:
        return "🟡 Medium Priority"
    else:
        return "🟢 Normal"


def _generate_recommendations(topics: list[dict], study_days: int) -> list[str]:
    """Generate smart study recommendations."""
    recommendations = []

    if study_days < len(topics):
        recommendations.append(
            "⚠️ You have more topics than available days. Consider combining related topics."
        )

    if study_days < 7:
        recommendations.append(
            "⏰ Time is tight! Focus on high-weight topics and practice problems."
        )

    high_weight = [t for t in topics if t.get("weight", 1.0) >= 2.0]
    if high_weight:
        names = ", ".join(t["name"] for t in high_weight[:3])
        recommendations.append(
            f"🎯 Priority topics (high exam weight): {names}"
        )

    recommendations.append(
        "💡 Use active recall: after studying a topic, close your notes and try to explain it."
    )
    recommendations.append(
        "🔄 Review previous topics briefly each day to reinforce learning."
    )

    return recommendations
