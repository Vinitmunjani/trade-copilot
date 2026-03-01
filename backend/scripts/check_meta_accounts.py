import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import asyncio
from sqlalchemy import select
from app.database import async_session_factory, init_db
from app.models.user import User
from app.models.meta_account import MetaAccount

async def main():
    await init_db()
    async with async_session_factory() as db:
        res = await db.execute(select(User).where(User.email == 'trader@example.com'))
        user = res.scalar_one_or_none()
        if not user:
            print('User not found: trader@example.com')
            return
        print('User id:', user.id)
        res2 = await db.execute(select(MetaAccount).where(MetaAccount.user_id == user.id))
        rows = res2.scalars().all()
        print('MetaAccounts found:', len(rows))
        for r in rows:
            print(r.id, r.metaapi_account_id, r.mt_login, r.mt_server, r.mt_last_heartbeat)

asyncio.run(main())
