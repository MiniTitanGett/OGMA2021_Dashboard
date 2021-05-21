USE [OGMA_Test]
GO

CREATE TABLE [dbo].['OP_Char'](
    char_id int,
    person_id int,
    char_type varchar(64), -- 'DashboardExt' or 'ReportExt'
    char_type_qualifier varchar(64), -- Pointer
    char_value_text varchar(max),
)
GO