USE [OGMA_Test]
GO

/****** Object:  Table [dbo].['start_data']    Script Date: 2021-05-19 12:03:31 PM ******/

CREATE TABLE [dbo].['start_data'](
	ref_value varchar(max) ,
	language varchar(2),
	ref_desc varchar(max),
	

) ON [PRIMARY]
GO

--BULK 
--INSERT [dbo].['start_data']
--FROM 'C:\Users\derek\OGMA2021_Dashboard\apps\OPG001\test_data\Language Data JG.csv'
--WITH (FORMAT='CSV');

BULK INSERT [dbo].['start_data']  
FROM 'C:\Users\derek\OGMA2021_Dashboard\apps\OPG001\test_data\Language Data JG.csv'
WITH  
(  
FIRSTROW = 2,  
DATAFILETYPE = 'char',  
MAXERRORS = 100,  
FIELDTERMINATOR = ',',  
ROWTERMINATOR = '\n'  
);

SELECT * FROM [dbo].['start_data'] ;