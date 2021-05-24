USE [OGMA_Test]
GO

/****** Object:  Table [dbo].[OP_Ref]    Script Date: 2021-05-19 10:29:31 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[OP_Ref](
	ref_id int unique NOT NULL IDENTITY(1,1) ,
	ref_table varchar(64) NOT NULL ,
	ref_value varchar(64) NOT NULL ,
	language varchar(20) NOT NULL ,
	ref_desc varchar(max) NOT NULL ,
	CONSTRAINT PK_reftable PRIMARY KEY (ref_table,ref_value,language)

) ON [PRIMARY]
GO


