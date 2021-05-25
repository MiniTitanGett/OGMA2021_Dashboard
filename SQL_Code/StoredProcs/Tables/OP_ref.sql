USE [OGMA_Test]
GO
DROP TABLE [dbo].[OP_ref_insert]
/****** Object:  Table [dbo].[OP_ref_insert]    Script Date: 2021-05-19 12:03:31 PM ******/
CREATE TABLE [dbo].[OP_ref_insert](
	
	ref_table varchar(max) NOT NULL ,
	ref_value varchar(max) NOT NULL ,
	language varchar(20) NOT NULL ,
	ref_desc varchar(max) NOT NULL ,
	--CONSTRAINT PK_reftable PRIMARY KEY (ref_table,ref_value,language)

) ON [PRIMARY]
GO

BULK INSERT [dbo].[OP_ref_insert]
FROM 'C:\Users\derek\OGMA2021_Dashboard\apps\OPG001\test_data\Modified Language Data JG.csv'
WITH  
(  
FIRSTROW = 2,  
DATAFILETYPE = 'char',  
MAXERRORS = 100,  
FIELDTERMINATOR = ',',  
ROWTERMINATOR = '\n'  
);
go

UPDATE [dbo].[OP_ref_insert]
SET    ref_value = REPLACE(ref_value, ' ', '_')
WHERE  ref_value LIKE '%[ ]%'
go

Create Proc dbo.spreftable

as

Select  [dbo].[OP_Ref].ref_id, [dbo].[OP_ref_insert].ref_table,[dbo].[OP_ref_insert].ref_value, [dbo].[OP_ref_insert].language, [dbo].[OP_ref_insert].ref_desc
FROM [dbo].[OP_ref_insert] LEFT JOIN [dbo].[OP_Ref] ON
([dbo].[OP_ref_insert].ref_table=[dbo].[OP_Ref].ref_table AND [dbo].[OP_ref_insert].ref_value=[dbo].[OP_Ref].ref_value AND [dbo].[OP_ref_insert].language=[dbo].[OP_Ref].language AND[dbo].[OP_ref_insert].ref_desc=[dbo].[OP_Ref].ref_desc)


go

/*
exec dbo.spreftable
go*/