Use [OGMA_Test]
GO

BEGIN
	EXEC('
		Create PROCEDURE dbo.spOPref_getOPrefdata
			@Table Varchar(60),
			@lang Varchar(60) --Lang Short for Language

		AS
			BEGIN
			SELECT ref_value, ref_desc
			From [dbo].[OP_Ref]
			Where [dbo].[OP_Ref].ref_table= @Table AND [dbo].[OP_Ref].[language] = @lang;
			END')

END
GO

/*
EXEC dbo.spOPref_getOPrefdata @Table= N'Labels', @lang=N'En';

go*/