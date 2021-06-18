IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[OPG010_NodeData]') AND type in (N'U'))
DROP TABLE [dbo].[OPG010_NodeData]
GO

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[OPG010_NodeData](
  [node_id] varchar(64) NOT NULL,
  [x_coord] numeric(4, 3) NOT NULL,
  [y_coord] numeric(4, 3) NOT NULL,
  [colour] varchar(64) NOT NULL
) ON [PRIMARY]
GO


-- EOF