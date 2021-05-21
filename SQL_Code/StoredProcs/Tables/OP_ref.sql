USE [OGMA_Test]
GO
DROP TABLE [dbo].['OP_ref']
/****** Object:  Table [dbo].['Ref ']    Script Date: 2021-05-19 12:03:31 PM ******/
CREATE TABLE [dbo].['OP_ref'](
	
	ref_table varchar(max) NOT NULL ,
	ref_value varchar(max) NOT NULL ,
	language varchar(20) NOT NULL ,
	ref_desc varchar(max) NOT NULL ,
	--CONSTRAINT PK_reftable PRIMARY KEY (ref_table,ref_value,language)

) ON [PRIMARY]
GO

BULK INSERT [dbo].['OP_ref']  
FROM 'C:\Users\derek\OGMA2021_Dashboard\apps\OPG001\test_data\Modified Language Data JG.csv'
WITH  
(  
FIRSTROW = 2,  
DATAFILETYPE = 'char',  
MAXERRORS = 100,  
FIELDTERMINATOR = ',',  
ROWTERMINATOR = '\n'  
);

UPDATE [dbo].['OP_ref'] 
SET    ref_value = REPLACE(ref_value, ' ', '_')
WHERE  ref_value LIKE '%[ ]%'

Select  [dbo].['OP Ref table'].ref_id, [dbo].['OP_ref'].ref_table,[dbo].['OP_ref'].ref_value, [dbo].['OP_ref'].language, [dbo].['OP_ref'].ref_desc
FROM [dbo].['OP_ref'] LEFT JOIN [dbo].['OP Ref table'] ON 
([dbo].['OP_ref'].ref_table=[dbo].['OP Ref table'].ref_table AND [dbo].['OP_ref'].ref_value=[dbo].['OP Ref table'].ref_value AND [dbo].['OP_ref'].language=[dbo].['OP Ref table'].language AND[dbo].['OP_ref'].ref_desc=[dbo].['OP Ref table'].ref_desc)

SELECT * FROM [dbo].['OP_ref'] ;