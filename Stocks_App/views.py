from datetime import datetime

from django.db import connection
from django.shortcuts import render


def Home(request):
    return render(request, 'Home.html')


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def Query_res(request):
    with connection.cursor() as cursor:
        cursor.execute("""
                select i.Name, ROUND(sum(b.BQuantity * s.Price), 3) as total_sum
                from Buying b join Stock s on (b.tDate = s.tDate and b.Symbol = s.Symbol),Versatile_investors i
                where b.id = i.ID
                group by i.Name
                order by total_sum desc
                ;      
        """)
        sql_res1 = dictfetchall(cursor)

    with connection.cursor() as cursor:
        cursor.execute("""
                 select *
                 from buyers_of_PC b
                 where b.total_quantity >= ALL (select b1.total_quantity
                                from buyers_of_PC b1
                                where b1.symbol = b.symbol)
                 order by b.symbol,b.name;
        """)
        sql_res2 = dictfetchall(cursor)
    with connection.cursor() as cursor:
        cursor.execute("""
                        select distinct(c.tDate), c.symbol, i.Name
                        from before_last_date c, Stock s, investor i, dates d
                        where s.symbol= c.symbol and s.tDate = (select Min(d1.tdate)
                        from Dates d1
                        where c.tDate < d1.tdate) and s.price > 1.03*c.price and i.id = c.id;
                    """)
        sql_res4 = dictfetchall(cursor)
    return render(request, 'Query_Results.html', {'sql_res1': sql_res1, 'sql_res2': sql_res2, 'sql_res4': sql_res4})


def add_transactions(request):
    if request.method == 'POST' and request.POST:
        id = int(request.POST["id"])
        transaction = int(request.POST["transaction"])
        with connection.cursor() as cursor:
            sql = """select i.id
                     from investor i
                     where i.id = %s;
             """
            cursor.execute(sql, params=[id])
            sql_res3 = dictfetchall(cursor)
        if not sql_res3:
            return render(request, 'Add_Transactions.html', {'sql_res1': sql_res1, 'sql_res3': sql_res3})
        with connection.cursor() as cursor:
            sql = """
                    select t.tDate, t.id,t.TQuantity
                    from Transactions t
                    where t.tdate = %s and t.id =%s;
            """
            cursor.execute(sql, params=[datetime.today().strftime('%Y-%m-%d'), id])
            auxilery = dictfetchall(cursor)
            if auxilery:
                diff = auxilery[0].get('TQuantity')
                with connection.cursor() as cursor:
                    sql = """
                            DELETE FROM Transactions WHERE tDate = %s and id = %s;

                    """
                    cursor.execute(sql, params=[datetime.today().strftime('%Y-%m-%d'), id])
                with connection.cursor() as cursor:
                    sql = """
                            update Investor set AvailableCash = AvailableCash -%s
                     where id = %s;
                    """
                    cursor.execute(sql, params=[diff, id])
            with connection.cursor() as cursor:
                sql = """update Investor set AvailableCash = AvailableCash +%s
                         where id = %s;"""
                cursor.execute(sql, params=[transaction, id])
            with connection.cursor() as cursor:
                sql = """INSERT INTO Transactions (tDate, ID, TQuantity) VALUES (cast(%s AS DATETIME
                ),%s,%s);"""
                cursor.execute(sql, params=[datetime.today().strftime('%Y-%m-%d'), id, transaction])
    with connection.cursor() as cursor:
        cursor.execute("""
                select TOP 10 *
                from Transactions t
                order by t.tDate DESC, t.id DESC;    
        """)
        sql_res1 = dictfetchall(cursor)
    id = {'id': 1}
    sql_res3 = [id]
    return render(request, 'Add_Transactions.html', {'sql_res1': sql_res1, 'sql_res3': sql_res3})


def buy_stocks(request):
    fail1 = False
    fail2 = False
    fail3 = False
    fail4 = False
    if request.method == 'POST' and request.POST:
        id = int(request.POST["id"])
        symbol = str(request.POST["symbol"])
        quantity = int(request.POST["quantity"])
        with connection.cursor() as cursor:
            sql = """select i.id
                     from investor i
                     where i.id = %s;
             """
            cursor.execute(sql, params=[id])
            sql_res1 = dictfetchall(cursor)
            if not sql_res1:
                fail1 = True
        with connection.cursor() as cursor:
            sql = """   select c.symbol
                        from Company c
                        where c.symbol = %s;
             """
            cursor.execute(sql, params=[symbol])
            sql_res2 = dictfetchall(cursor)
            if not sql_res2:
                fail2 = True
        with connection.cursor() as cursor:
            sql = """   select s.symbol, s.tdate
                        from Stock s
                        where s.symbol = %s and s.tdate =%s;
             """
            cursor.execute(sql, params=[symbol, datetime.today().strftime('%Y-%m-%d')])
            auxiliary = dictfetchall(cursor)
            if not auxiliary and not fail2:
                with connection.cursor() as cursor:
                    sql = """  INSERT INTO Stock (Symbol, tDate, Price) VALUES (%s, CAST(%s AS DATETIME), (SELECT s.Price
                                FROM Stock s
                                WHERE s.Symbol = %s AND s.tDate >= ALL(SELECT s1.tDate
                                       FROM Stock s1
                                       WHERE s1.Symbol = s.Symbol)));
                     """
                    cursor.execute(sql, params=[symbol, datetime.today().strftime('%Y-%m-%d'), symbol])
        if not fail1 and not fail2:
            with connection.cursor() as cursor:
                sql = """   select i.id
                            from Investor i
                            where i.id = %s and i.AvailableCash - %s*(select s.price
                                                                        from Stock s
                                                                        where s.symbol = %s and s.tDate= %s)>= 0;
                 """
                cursor.execute(sql, params=[id, quantity, symbol, datetime.today().strftime('%Y-%m-%d')])
                sql_res3 = dictfetchall(cursor)
                if not sql_res3:
                    fail3 = True
            with connection.cursor() as cursor:
                sql = """   select *
                            from Buying b
                            where b.id = %s and b.Symbol = %s and B.tDate = %s;
                 """
                cursor.execute(sql, params=[id, symbol, datetime.today().strftime('%Y-%m-%d')])
                sql_res4 = dictfetchall(cursor)
                if sql_res4:
                    fail4 = True
        if fail1 + fail2 + fail3 + fail4 == 0:
            with connection.cursor() as cursor:
                sql = """ INSERT INTO Buying (tDate, ID, Symbol, BQuantity) VALUES (CAST(%s AS DATETIME), %s, %s, %s)
                 """
                cursor.execute(sql, params=[datetime.today().strftime('%Y-%m-%d'), id, symbol, quantity])
            with connection.cursor() as cursor:
                sql = """ UPDATE Investor SET AvailableCash = AvailableCash - %s*(select s.price
                                                                    from Stock s
                                                                    where s.symbol = %s and s.tDate= %s) WHERE ID = %s;
                 """
                cursor.execute(sql, params=[quantity, symbol, datetime.today().strftime('%Y-%m-%d'), id])
    with connection.cursor() as cursor:
        sql = """select top 10 b.tdate,b.id ,b.Symbol, ROUND((b.BQuantity*s.Price),3) as sum_total
                 from Buying b, stock s
                 where b.tDate =s.tDate and b.Symbol = s.Symbol
                 order by sum_total desc;
         """
        cursor.execute(sql)
        sql_res5 = dictfetchall(cursor)
    return render(request, 'Buy_Stocks.html',
                  {'fail1': fail1, 'fail2': fail2, 'fail3': fail3, 'fail4': fail4, 'sql_res5': sql_res5})
