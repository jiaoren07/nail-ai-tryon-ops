"""Quick diagnostic: are emerging_hot styles still meeting Step 6.2 rules?"""
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from sqlalchemy import text
from app.db import async_session_maker


async def go():
    async with async_session_maker() as db:
        print("=== date range of tryons ===")
        r = await db.execute(text(
            "SELECT MIN(date(created_at,'localtime')), MAX(date(created_at,'localtime')) FROM tryons"
        ))
        print(" ", r.first())

        for label, sql in [
            ("recent 3 days per emerging style", "SELECT style_id, COUNT(*) FROM tryons WHERE created_at >= datetime('now','-3 days') AND style_id IN ('f_09','f_15','m_15') GROUP BY style_id"),
            ("previous 3 days per emerging style", "SELECT style_id, COUNT(*) FROM tryons WHERE created_at >= datetime('now','-6 days') AND created_at < datetime('now','-3 days') AND style_id IN ('f_09','f_15','m_15') GROUP BY style_id"),
            ("last 24h per emerging style", "SELECT style_id, COUNT(*) FROM tryons WHERE created_at >= datetime('now','-1 day') AND style_id IN ('f_09','f_15','m_15') GROUP BY style_id"),
            ("last 24h per ALL style (top10)", "SELECT style_id, COUNT(*) AS c FROM tryons WHERE created_at >= datetime('now','-1 day') GROUP BY style_id ORDER BY c DESC LIMIT 10"),
            ("collect rate last 3d (emerging)", "SELECT style_id, SUM(CASE WHEN is_collected=1 THEN 1 ELSE 0 END), COUNT(*) FROM tryons WHERE created_at >= datetime('now','-3 days') AND style_id IN ('f_09','f_15','m_15') GROUP BY style_id"),
        ]:
            print(f"\n=== {label} ===")
            r = await db.execute(text(sql))
            for row in r.all():
                print(" ", row)


asyncio.run(go())
