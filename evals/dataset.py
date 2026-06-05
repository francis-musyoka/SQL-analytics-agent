"""Each case is a question plus a GOLD SQL query (hand-verified correct).
We score by running the agent, then comparing its result set to the gold's.

GROUND-TRUTH RULE: every gold_sql here was run read-only against THIS repo's
data/chinook.db and its answer confirmed. If the database is ever swapped, the
gold queries must be re-verified — answers depend on the Chinook version.

DESIGN NOTES (so the score stays meaningful):
- Execution accuracy compares RESULT SETS (order-insensitive), so column aliases
  and row order don't matter. What matters for LIMIT queries is WHICH rows come
  back, so "top N" golds use deterministic tiebreakers (e.g. ORDER BY ..., Name)
  and are chosen so the Nth/N+1th rows are not tied.
- We favor single-value aggregate answers (COUNT/SUM/MAX/AVG) where possible —
  they cannot be ambiguous.
"""
EVAL_CASES = [
    # --- simple counts (single-value, unambiguous) ---
    {"question": "How many tracks are in the database?",
     "gold_sql": "SELECT COUNT(*) FROM Track"},
    {"question": "How many albums are there?",
     "gold_sql": "SELECT COUNT(*) FROM Album"},
    {"question": "How many artists are in the database?",
     "gold_sql": "SELECT COUNT(*) FROM Artist"},
    {"question": "How many customers are there?",
     "gold_sql": "SELECT COUNT(*) FROM Customer"},
    {"question": "How many employees are there?",
     "gold_sql": "SELECT COUNT(*) FROM Employee"},
    {"question": "How many invoices are there in total?",
     "gold_sql": "SELECT COUNT(*) FROM Invoice"},
    {"question": "How many genres are there?",
     "gold_sql": "SELECT COUNT(*) FROM Genre"},
    {"question": "How many playlists are there?",
     "gold_sql": "SELECT COUNT(*) FROM Playlist"},
    {"question": "How many media types are there?",
     "gold_sql": "SELECT COUNT(*) FROM MediaType"},
    {"question": "How many invoice line items are there?",
     "gold_sql": "SELECT COUNT(*) FROM InvoiceLine"},

    # --- filtered counts (WHERE) ---
    {"question": "How many customers are from Canada?",
     "gold_sql": "SELECT COUNT(*) FROM Customer WHERE Country = 'Canada'"},
    {"question": "How many customers are from the USA?",
     "gold_sql": "SELECT COUNT(*) FROM Customer WHERE Country = 'USA'"},
    {"question": "How many customers are from Brazil?",
     "gold_sql": "SELECT COUNT(*) FROM Customer WHERE Country = 'Brazil'"},
    {"question": "How many tracks have no composer listed?",
     "gold_sql": "SELECT COUNT(*) FROM Track WHERE Composer IS NULL"},
    {"question": "How many tracks are longer than 5 minutes (300000 ms)?",
     "gold_sql": "SELECT COUNT(*) FROM Track WHERE Milliseconds > 300000"},
    {"question": "How many employees have the title 'Sales Support Agent'?",
     "gold_sql": "SELECT COUNT(*) FROM Employee WHERE Title = 'Sales Support Agent'"},
    {"question": "How many invoices were billed to the USA?",
     "gold_sql": "SELECT COUNT(*) FROM Invoice WHERE BillingCountry = 'USA'"},
    {"question": "How many albums does the artist 'AC/DC' have?",
     "gold_sql": "SELECT COUNT(*) FROM Album a JOIN Artist ar ON a.ArtistId = ar.ArtistId WHERE ar.Name = 'AC/DC'"},
    {"question": "How many tracks belong to the 'Rock' genre?",
     "gold_sql": "SELECT COUNT(*) FROM Track t JOIN Genre g ON t.GenreId = g.GenreId WHERE g.Name = 'Rock'"},
    {"question": "How many tracks have the media type 'Protected AAC audio file'?",
     "gold_sql": "SELECT COUNT(*) FROM Track t JOIN MediaType m ON t.MediaTypeId = m.MediaTypeId WHERE m.Name = 'Protected AAC audio file'"},

    # --- aggregates (single value) ---
    {"question": "What is the total revenue from all invoices?",
     "gold_sql": "SELECT SUM(Total) FROM Invoice"},
    {"question": "What is the average invoice total?",
     "gold_sql": "SELECT AVG(Total) FROM Invoice"},
    {"question": "What is the length in milliseconds of the longest track?",
     "gold_sql": "SELECT MAX(Milliseconds) FROM Track"},
    {"question": "What is the lowest unit price among all tracks?",
     "gold_sql": "SELECT MIN(UnitPrice) FROM Track"},
    {"question": "What is the average track length in milliseconds?",
     "gold_sql": "SELECT AVG(Milliseconds) FROM Track"},
    {"question": "What is the total quantity of all items sold?",
     "gold_sql": "SELECT SUM(Quantity) FROM InvoiceLine"},
    {"question": "How many distinct countries do customers come from?",
     "gold_sql": "SELECT COUNT(DISTINCT Country) FROM Customer"},
    {"question": "What is the highest single invoice total?",
     "gold_sql": "SELECT MAX(Total) FROM Invoice"},

    # --- group-by returning ONE name (single value) ---
    {"question": "Which genre has the most tracks? Return its name.",
     "gold_sql": "SELECT g.Name FROM Genre g JOIN Track t ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY COUNT(*) DESC, g.Name ASC LIMIT 1"},
    {"question": "Which country has the most customers? Return the country name.",
     "gold_sql": "SELECT Country FROM Customer GROUP BY Country ORDER BY COUNT(*) DESC, Country ASC LIMIT 1"},
    {"question": "Which media type is used by the most tracks? Return its name.",
     "gold_sql": "SELECT m.Name FROM MediaType m JOIN Track t ON t.MediaTypeId = m.MediaTypeId GROUP BY m.MediaTypeId ORDER BY COUNT(*) DESC, m.Name ASC LIMIT 1"},
    {"question": "Which artist has the most albums? Return the artist name.",
     "gold_sql": "SELECT ar.Name FROM Artist ar JOIN Album a ON a.ArtistId = ar.ArtistId GROUP BY ar.ArtistId ORDER BY COUNT(*) DESC, ar.Name ASC LIMIT 1"},

    # --- single lookups ---
    {"question": "What is the name of the longest track (by milliseconds)?",
     "gold_sql": "SELECT Name FROM Track ORDER BY Milliseconds DESC, Name ASC LIMIT 1"},
    {"question": "What is the title of the album with the most tracks?",
     "gold_sql": "SELECT al.Title FROM Album al JOIN Track t ON t.AlbumId = al.AlbumId GROUP BY al.AlbumId ORDER BY COUNT(*) DESC, al.Title ASC LIMIT 1"},
    {"question": "What is the first and last name of the employee who is the General Manager?",
     "gold_sql": "SELECT FirstName, LastName FROM Employee WHERE Title = 'General Manager'"},
    {"question": "Which customer has the email 'luisg@embraer.com.br'? Return first and last name.",
     "gold_sql": "SELECT FirstName, LastName FROM Customer WHERE Email = 'luisg@embraer.com.br'"},

    # --- top N (deterministic tiebreakers; boundaries verified non-tied) ---
    {"question": "What are the names of the 5 longest tracks by milliseconds?",
     "gold_sql": "SELECT Name FROM Track ORDER BY Milliseconds DESC, Name ASC LIMIT 5"},
    {"question": "Which 5 genres have the most tracks? Return their names.",
     "gold_sql": "SELECT g.Name FROM Genre g JOIN Track t ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY COUNT(*) DESC, g.Name ASC LIMIT 5"},
    {"question": "Which 3 countries have the highest total invoice amounts? Return country names.",
     "gold_sql": "SELECT BillingCountry FROM Invoice GROUP BY BillingCountry ORDER BY SUM(Total) DESC, BillingCountry ASC LIMIT 3"},
    {"question": "Who are the top 3 customers by total spend? Return first and last name.",
     "gold_sql": "SELECT c.FirstName, c.LastName FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId GROUP BY c.CustomerId ORDER BY SUM(i.Total) DESC, c.CustomerId ASC LIMIT 3"},
    {"question": "Which 3 artists have the most tracks? Return their names.",
     "gold_sql": "SELECT ar.Name FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId JOIN Track t ON t.AlbumId = al.AlbumId GROUP BY ar.ArtistId ORDER BY COUNT(*) DESC, ar.Name ASC LIMIT 3"},
    {"question": "Which 4 albums have the most tracks? Return their titles.",
     "gold_sql": "SELECT al.Title FROM Album al JOIN Track t ON t.AlbumId = al.AlbumId GROUP BY al.AlbumId ORDER BY COUNT(*) DESC, al.Title ASC LIMIT 4"},
    {"question": "How many distinct tracks have been sold (appear in invoice lines)?",
     "gold_sql": "SELECT COUNT(DISTINCT TrackId) FROM InvoiceLine"},
    {"question": "How many tracks have a unit price of 0.99?",
     "gold_sql": "SELECT COUNT(*) FROM Track WHERE UnitPrice = 0.99"},

    # --- date-based ---
    {"question": "How many invoices were created in 2021?",
     "gold_sql": "SELECT COUNT(*) FROM Invoice WHERE InvoiceDate >= '2021-01-01' AND InvoiceDate < '2022-01-01'"},
    {"question": "How many invoices were created in 2022?",
     "gold_sql": "SELECT COUNT(*) FROM Invoice WHERE InvoiceDate >= '2022-01-01' AND InvoiceDate < '2023-01-01'"},
    {"question": "What was the total revenue in 2021?",
     "gold_sql": "SELECT SUM(Total) FROM Invoice WHERE InvoiceDate >= '2021-01-01' AND InvoiceDate < '2022-01-01'"},

    # --- a few more joins / distinct ---
    {"question": "How many tracks are on the playlist named 'On-The-Go 1'?",
     "gold_sql": "SELECT COUNT(*) FROM PlaylistTrack pt JOIN Playlist p ON p.PlaylistId = pt.PlaylistId WHERE p.Name = 'On-The-Go 1'"},
    {"question": "How many distinct genres appear in the Track table?",
     "gold_sql": "SELECT COUNT(DISTINCT GenreId) FROM Track WHERE GenreId IS NOT NULL"},
    {"question": "How many customers does the support rep 'Jane Peacock' serve?",
     "gold_sql": "SELECT COUNT(*) FROM Customer c JOIN Employee e ON c.SupportRepId = e.EmployeeId WHERE e.FirstName = 'Jane' AND e.LastName = 'Peacock'"},
]


# HARD tier: multi-hop joins, nested aggregation, negation, date math, and
# schema/phrasing traps. These deliberately stress the agent so the score has
# headroom (the easy 50 above all pass). Same ground-truth rule: every gold_sql
# was run read-only against this repo's data/chinook.db and verified
# deterministic (single-value answers where possible; tiebreakers on top-N).
HARD_CASES = [
    # --- multi-hop joins (3-4 tables) ---
    {"question": "Which artist has the most tracks in the 'Rock' genre? Return the artist name.",
     "gold_sql": "SELECT ar.Name FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId JOIN Track t ON t.AlbumId = al.AlbumId JOIN Genre g ON t.GenreId = g.GenreId WHERE g.Name = 'Rock' GROUP BY ar.ArtistId ORDER BY COUNT(*) DESC, ar.Name ASC LIMIT 1"},
    {"question": "Which genre generates the most revenue? Return its name.",
     "gold_sql": "SELECT g.Name FROM Genre g JOIN Track t ON t.GenreId = g.GenreId JOIN InvoiceLine il ON il.TrackId = t.TrackId GROUP BY g.GenreId ORDER BY SUM(il.UnitPrice * il.Quantity) DESC, g.Name ASC LIMIT 1"},
    {"question": "Which 3 artists generated the most revenue? Return their names.",
     "gold_sql": "SELECT ar.Name FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId JOIN Track t ON t.AlbumId = al.AlbumId JOIN InvoiceLine il ON il.TrackId = t.TrackId GROUP BY ar.ArtistId ORDER BY SUM(il.UnitPrice * il.Quantity) DESC, ar.Name ASC LIMIT 3"},
    {"question": "Which sales support agent is responsible for the most revenue? Return first and last name.",
     "gold_sql": "SELECT e.FirstName, e.LastName FROM Employee e JOIN Customer c ON c.SupportRepId = e.EmployeeId JOIN Invoice i ON i.CustomerId = c.CustomerId GROUP BY e.EmployeeId ORDER BY SUM(i.Total) DESC, e.EmployeeId ASC LIMIT 1"},
    {"question": "Which media type generates the most revenue? Return its name.",
     "gold_sql": "SELECT m.Name FROM MediaType m JOIN Track t ON t.MediaTypeId = m.MediaTypeId JOIN InvoiceLine il ON il.TrackId = t.TrackId GROUP BY m.MediaTypeId ORDER BY SUM(il.UnitPrice * il.Quantity) DESC, m.Name ASC LIMIT 1"},
    {"question": "How many customers have spent more than 45 dollars in total?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT i.CustomerId, SUM(i.Total) s FROM Invoice i GROUP BY i.CustomerId) WHERE s > 45"},
    {"question": "Which artist has the longest total track playtime? Return the artist name.",
     "gold_sql": "SELECT ar.Name FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId JOIN Track t ON t.AlbumId = al.AlbumId GROUP BY ar.ArtistId ORDER BY SUM(t.Milliseconds) DESC, ar.Name ASC LIMIT 1"},

    # --- nested aggregation (aggregate of an aggregate) ---
    {"question": "How many customers have spent more than the average customer's total spend?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT i.CustomerId, SUM(i.Total) s FROM Invoice i GROUP BY i.CustomerId) WHERE s > (SELECT AVG(t) FROM (SELECT SUM(i2.Total) t FROM Invoice i2 GROUP BY i2.CustomerId))"},
    {"question": "How many tracks are longer than the average track length?",
     "gold_sql": "SELECT COUNT(*) FROM Track WHERE Milliseconds > (SELECT AVG(Milliseconds) FROM Track)"},
    {"question": "What is the maximum number of tracks on any single album?",
     "gold_sql": "SELECT MAX(c) FROM (SELECT COUNT(*) c FROM Track WHERE AlbumId IS NOT NULL GROUP BY AlbumId)"},
    {"question": "How many customers from the USA have spent more than 40 dollars in total?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT c.CustomerId, SUM(i.Total) s FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId WHERE c.Country = 'USA' GROUP BY c.CustomerId) WHERE s > 40"},
    {"question": "How many albums contain exactly one track?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT AlbumId FROM Track WHERE AlbumId IS NOT NULL GROUP BY AlbumId HAVING COUNT(*) = 1)"},
    {"question": "How many invoices have more than 5 line items?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT InvoiceId FROM InvoiceLine GROUP BY InvoiceId HAVING COUNT(*) > 5)"},
    {"question": "How many playlists contain more than 100 tracks?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT PlaylistId FROM PlaylistTrack GROUP BY PlaylistId HAVING COUNT(*) > 100)"},

    # --- negation / absence ---
    {"question": "How many artists have no albums?",
     "gold_sql": "SELECT COUNT(*) FROM Artist ar WHERE NOT EXISTS (SELECT 1 FROM Album al WHERE al.ArtistId = ar.ArtistId)"},
    {"question": "How many tracks have never been purchased?",
     "gold_sql": "SELECT COUNT(*) FROM Track t WHERE NOT EXISTS (SELECT 1 FROM InvoiceLine il WHERE il.TrackId = t.TrackId)"},
    {"question": "How many genres have no tracks?",
     "gold_sql": "SELECT COUNT(*) FROM Genre g WHERE NOT EXISTS (SELECT 1 FROM Track t WHERE t.GenreId = g.GenreId)"},

    # --- revenue / business questions (revenue = UnitPrice * Quantity) ---
    {"question": "What is the total revenue generated by tracks in the 'Rock' genre?",
     "gold_sql": "SELECT SUM(il.UnitPrice * il.Quantity) FROM InvoiceLine il JOIN Track t ON t.TrackId = il.TrackId JOIN Genre g ON t.GenreId = g.GenreId WHERE g.Name = 'Rock'"},
    {"question": "What is the total revenue from customers in Brazil?",
     "gold_sql": "SELECT SUM(Total) FROM Invoice WHERE BillingCountry = 'Brazil'"},
    {"question": "What is the total revenue from customers served by the support rep 'Jane Peacock'?",
     "gold_sql": "SELECT SUM(i.Total) FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId JOIN Employee e ON c.SupportRepId = e.EmployeeId WHERE e.FirstName = 'Jane' AND e.LastName = 'Peacock'"},
    {"question": "Who is the single best customer by total spend? Return first and last name.",
     "gold_sql": "SELECT c.FirstName, c.LastName FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId GROUP BY c.CustomerId ORDER BY SUM(i.Total) DESC, c.CustomerId ASC LIMIT 1"},

    # --- date math ---
    {"question": "Which year had the highest total sales? Return the year.",
     "gold_sql": "SELECT strftime('%Y', InvoiceDate) y FROM Invoice GROUP BY y ORDER BY SUM(Total) DESC, y ASC LIMIT 1"},
    {"question": "How many invoices were issued in the first quarter of 2021 (January through March)?",
     "gold_sql": "SELECT COUNT(*) FROM Invoice WHERE InvoiceDate >= '2021-01-01' AND InvoiceDate < '2021-04-01'"},
    {"question": "What was the total revenue in December 2022?",
     "gold_sql": "SELECT SUM(Total) FROM Invoice WHERE InvoiceDate >= '2022-12-01' AND InvoiceDate < '2023-01-01'"},

    # --- multi-filter ---
    {"question": "How many tracks in the 'Rock' genre are longer than 5 minutes (300000 ms)?",
     "gold_sql": "SELECT COUNT(*) FROM Track t JOIN Genre g ON t.GenreId = g.GenreId WHERE g.Name = 'Rock' AND t.Milliseconds > 300000"},

    # --- schema / unit traps (the NL word doesn't map to the obvious column/unit) ---
    {"question": "What is the average track length in seconds, rounded to the nearest whole number?",
     "gold_sql": "SELECT ROUND(AVG(Milliseconds) / 1000.0) FROM Track"},
    {"question": "What is the length of the longest track in whole minutes (rounded down)?",
     "gold_sql": "SELECT MAX(Milliseconds) / 60000 FROM Track"},
    {"question": "On average, how many tracks does an album have? Round to one decimal place.",
     "gold_sql": "SELECT ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT AlbumId), 1) FROM Track WHERE AlbumId IS NOT NULL"},

    # --- hierarchy / self-reference ---
    {"question": "How many employees report directly to the General Manager?",
     "gold_sql": "SELECT COUNT(*) FROM Employee WHERE ReportsTo = (SELECT EmployeeId FROM Employee WHERE Title = 'General Manager')"},
    {"question": "Which album has the highest average track length? Return its title.",
     "gold_sql": "SELECT al.Title FROM Album al JOIN Track t ON t.AlbumId = al.AlbumId GROUP BY al.AlbumId ORDER BY AVG(t.Milliseconds) DESC, al.Title ASC LIMIT 1"},
]

