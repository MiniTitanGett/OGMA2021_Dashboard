CREATE PROCEDURE OP_AddGetEditDeleteFind_Char

	@person_id int,
	@char_type varchar(20),
	@char_type_qualifier varchar(30)

	AS

	SELECT char_type, char_type_qualifier, char_value_text
	FROM [dbo].[OP_Char]
	where [dbo].[OP_Char].person_id=@person_id AND [dbo].[OP_Char].char_type=@char_type AND [dbo].[OP_Char].char_type_qualifier=@char_type_qualifier
GO
