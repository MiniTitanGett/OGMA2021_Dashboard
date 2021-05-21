USE [OGMA_Test];
GO

/****** Object:  Table [dbo].['OP_Curr_Sessions']    Script Date: 2021-05-21 1:15:51 PM ******/

CREATE TABLE [dbo].['OP_Curr_Sessions'](
	session_id int NOT NULL,
	person_id int NOT NULL,
) ON [PRIMARY];
GO

DECLARE @sid INTEGER;
DECLARE @pid INTEGER;
DECLARE @counter INTEGER;

SET @sid = 100;
SET @pid = 200;
SET @counter = 1;

WHILE @counter <= 10
BEGIN
    INSERT INTO [dbo].['OP_Curr_Sessions']
    VALUES (@sid + @counter, @pid + @counter);
    SET @counter = @counter + 1;
END;

GO

-- Test
SELECT * FROM [dbo].['OP_Curr_Sessions'] ;