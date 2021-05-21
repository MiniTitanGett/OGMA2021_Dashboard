Use [OGMA_Test]
GO

Create PROCEDURE dbo.spOPref_getOPrefdata
	@Table Varchar(60),
	@lang Varchar(60) --Lang Short for Language

AS

	SELECT ref_value, ref_desc
	From [dbo].['OP_ref'] 
	Where [dbo].['OP_ref'].ref_table= @Table AND [dbo].['OP_ref'].language= @lang;

GO

/*
EXEC dbo.spOPref_getOPrefdata @Table= N'Labels', @lang=N'En';

go*/