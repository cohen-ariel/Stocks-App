create view Versatile_investors
as
select b.id,i.name
from Company c, Buying b, investor i
where (select count(distinct(c1.Sector))
    from Buying b1, Company c1
    where b1.ID =b.ID and b1.tDate = b.tDate and b1.Symbol = c1.symbol)>=8 and i.id = b.id
group by b.id, i.name;



create view Popular_companies
as
select c.Symbol, count(distinct(b.tDate)) as total
from Company c, Buying b
where b.Symbol = c.Symbol
group by c.Symbol
having 2*count(distinct(b.tDate)) > (select count(distinct(b1.tDate))
                from buying b1
                );


create view buyers_of_PC
AS
select c1.symbol,i.name, sum(b1.BQuantity) as total_quantity
from buying b1, Popular_companies c1, investor i
where b1.symbol = c1.Symbol and i.ID = b1.ID
group by c1.symbol,i.name
having sum(b1.BQuantity)>10;

create view Dates
as
select distinct(s.tDate) as tdate
from Stock s
;

create view bought_only_once
as
select b.symbol
from Buying b
group by b.symbol
having count(b.tDate) = 1;

create view before_last_date
as
select c.symbol, b.tDate, b.id, s.price
from bought_only_once c , buying b, Stock s
where b.Symbol = c.symbol and c.symbol = s.Symbol  and b.tDate < (select max(d.tdate)
                                         from Dates d) and s.tDate= b.tdate;



