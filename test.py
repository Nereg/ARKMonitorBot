import asyncio
import aiomysql


async def test_example(loop):
    pool = await aiomysql.create_pool(host='127.0.0.1', port=3306,
                                      user='root', password='secret',
                                      db='bot', loop=loop)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("INSERT INTO `settings`(`GuildId`, `Prefix`, `Data`, `Admins`) VALUES (%s,'%s','%s','%s')",(123,'','',''))
            r = await cur.fetchall()
            print(r)          
            await cur.execute('commit')
            await cur.close()
            conn.close()
    pool.close()
    await pool.wait_closed()


loop = asyncio.get_event_loop()
loop.run_until_complete(test_example(loop))