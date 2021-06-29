USE [OGMA_Test]
GO

IF OBJECT_ID('dbo.OP_Char') IS NOT NULL
	BEGIN
		PRINT 'OP_Char Table Exists'

    if (exists (select top 1 1 from dbo.op_char where char_id is null))
    begin

		  CREATE TABLE [dbo].[OP_Char_TEMP](
			  char_id int unique NOT NULL IDENTITY(1,1),
			  person_id int,
			  char_type varchar(64), -- 'DashboardExt' or 'ReportExt'
			  char_type_qualifier varchar(64), -- Pointer
			  char_value_text varchar(max),
		  )

      insert dbo.op_char_temp (person_id, char_type, char_type_qualifier, char_value_text)
      select person_id, char_type, char_type_qualifier, char_value_text
        from dbo.op_char

      drop table dbo.op_char

      execute sp_rename N'dbo.OP_Char_TEMP', N'OP_Char', 'OBJECT'

    end

	END
ELSE
	BEGIN
		CREATE TABLE [dbo].[OP_Char](
			char_id int unique NOT NULL IDENTITY(1,1),
			person_id int,
			char_type varchar(64), -- 'DashboardExt' or 'ReportExt'
			char_type_qualifier varchar(64), -- Pointer
			char_value_text varchar(max),
		)
	END
GO