USE [OPEN_Dev_Dashboard]
GO

/****** Object:  Table [dbo].[hierarchytype]    Script Date: 2021-05-19 10:29:31 AM ******/

IF OBJECT_ID('[dbo].[hierarchytype]') IS NOT NULL
    BEGIN
        PRINT'hierarchytype Table Exists'
    END

ELSE
    BEGIN
        CREATE TABLE [dbo].[hierarchytype](
	        hier_id int unique NOT NULL IDENTITY(1,1) ,
	        hier_table varchar(64) NOT NULL ,
	        hier_value varchar(64) NOT NULL ,
	        language varchar(20) NOT NULL ,
	        hier_desc varchar(max) NOT NULL ,
	        CONSTRAINT PK_hierarchytype PRIMARY KEY (hier_table,hier_value,language)

        ) ON [PRIMARY]
    END
GO
