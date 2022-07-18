USE [OPEN_Dev_Dashboard]
GO
if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[InsertHierarchyType]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[InsertHierarchyType]
go


/****** Object:  Table [dbo].[OP.InsertHierarchyType]    Script Date: 2021-05-19 12:03:31 PM ******/
CREATE PROC InsertHierarchyType(
    @hier_table varchar(64),
    @hier_value varchar(64),
    @language varchar(20),
    @hier_desc varchar(max))
AS
set nocount on
IF EXISTS(SELECT 'TRUE' FROM [dbo].[hierarchytype] WHERE @hier_table = [dbo].[hierarchytype].hier_table AND @hier_value =[dbo].[hierarchytype].hier_value AND @language = [dbo].[hierarchytype].language)
    BEGIN
    print('The Entry Already Exists Update Description')
    UPDATE [dbo].[hierarchytype] SET hier_desc = @hier_desc WHERE @hier_table = [dbo].[hierarchytype].hier_table AND
    @hier_value =[dbo].[hierarchytype].hier_value AND @language = [dbo].[hierarchytype].language
    END

ELSE
 BEGIN
    print('Entry added')
    INSERT into [dbo].[hierarchytype] (hier_table, hier_value, language, hier_desc)
    values (@hier_table,@hier_value,@language,@hier_desc)
END
GO

EXEC InsertHierarchyType @hier_table = 'OPG011', @hier_value = 'Organizations', @language = 'En', @hier_desc = 'Organizations'
EXEC InsertHierarchyType @hier_table = 'OPG011', @hier_value = 'Commodities', @language = 'En', @hier_desc = 'Commodities'
EXEC InsertHierarchyType @hier_table = 'OPG011', @hier_value = 'Geographies', @language = 'En', @hier_desc = 'Geographies'


GO

DROP PROC InsertHierarchyType
GO


IF OBJECT_ID('dbo.InsertHierarchyType') IS NOT NULL
    PRINT   'REFTABLE Procedure Exists'

ELSE
	BEGIN
		EXEC('
    Create Proc dbo.InsertHierarchyType

    as
	BEGIN
    Select * From [dbo].[hierarchytype]
		END')
	END
    GO
