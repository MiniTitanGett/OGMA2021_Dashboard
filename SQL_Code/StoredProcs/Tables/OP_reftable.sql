USE [OGMA_Test]
GO

/****** Object:  Table [dbo].['OP ref table']    Script Date: 2021-05-19 10:29:31 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].['OP Ref table'](
	ref_id int unique,
	ref_table varchar(64),
	ref_value varchar(64),
	language varchar(20),
	ref_desc varchar(max),
	CONSTRAINT PK_reftable PRIMARY KEY	(ref_table,ref_value,language) 

) ON [PRIMARY]
GO


