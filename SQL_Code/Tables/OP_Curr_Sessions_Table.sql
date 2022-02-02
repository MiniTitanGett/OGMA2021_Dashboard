USE [OPEN_Dev_Dashboard]
GO

/****** Object:  Table [dbo].[OP_Curr_Sessions]    Script Date: 2021-06-02 9:08:14 AM ******/
IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[OP_Curr_Sessions]') AND type in (N'U'))
DROP TABLE [dbo].[OP_Curr_Sessions]
GO

/****** Object:  Table [dbo].[OP_Curr_Sessions]    Script Date: 2021-06-02 9:08:14 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[OP_Curr_Sessions](
	[session_id] [int] NOT NULL,
	[person_id] [int] NOT NULL,
  [current_lang] varchar(20) NOT NULL,
) ON [PRIMARY]
GO