USE [OGMA_Test]
GO

IF OBJECT_ID('dbo.OP_Char') IS NOT NULL
	BEGIN
		PRINT 'OP_Char Table Exists'
	END
ELSE
	BEGIN
		CREATE TABLE [dbo].[OP_Char](
			char_id int,
			person_id int,
			char_type varchar(64), -- 'DashboardExt' or 'ReportExt'
			char_type_qualifier varchar(64), -- Pointer
			char_value_text varchar(max),
		)
	END
GO