USE [OGMA_Test];
GO

/****** Object:  Table [dbo].[OP_Curr_Sessions]    Script Date: 2021-05-21 1:15:51 PM ******/

declare @session_id int
declare @person_id int
declare @language varchar(20)

DECLARE @sid INTEGER;
DECLARE @pid INTEGER;
DECLARE @counter INTEGER;

SET @sid = 100;
SET @pid = 200;
SET @counter = 1;
set @language = 'En'

WHILE @counter <= 10
BEGIN
  set @session_id = @sid + @counter
  set @person_id = @pid + @counter

  if (not exists (select top 1 1
                    from dbo.op_curr_sessions
                  where session_id = @session_id
                    and person_id = @person_id))
    INSERT [dbo].[OP_Curr_Sessions]
    VALUES (@session_id, @person_id, @language)

  SET @counter = @counter + 1
END

set @sid = 110
set @pid = 210
set @counter = 1
set @language = 'Fr'

WHILE @counter <= 10
BEGIN
  set @session_id = @sid + @counter
  set @person_id = @pid + @counter

  if (not exists (select top 1 1
                    from dbo.op_curr_sessions
                  where session_id = @session_id
                    and person_id = @person_id))
    INSERT [dbo].[OP_Curr_Sessions]
    VALUES (@session_id, @person_id, @language)

  SET @counter = @counter + 1
END

GO

-- Test
SELECT * FROM [dbo].[OP_Curr_Sessions] order by session_id