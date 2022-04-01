if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[OPP_Get_Org_Parent]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[OPP_Get_Org_Parent]
go

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[OPP_Get_Hierarchy_Parent]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[OPP_Get_Hierarchy_Parent]
go

-- Copyright � OGMA Consulting Corp.
-- $Id$
Create Procedure dbo.OPP_Get_Hierarchy_Parent

@pr_session_id   int,
@pr_language     varchar(20),
@pr_child        varchar(64),
@pr_child_level  int,
@p_parent        varchar(64)  output,
@p_result_status varchar(255) output

as
begin
  set nocount on

  set @p_result_status = 'NoOK'

  set @p_parent = null

  if (@pr_child_level = 5)
    set @p_parent = (select top 1 [Hierarchy One -4] from dbo.OPG011_eventData  with (nolock) where [Hierarchy One Leaf] = @pr_child)

  else if (@pr_child_level = 4)
    set @p_parent = (select top 1 [Hierarchy One -3] from dbo.OPG011_eventData  with (nolock) where [Hierarchy One -4] = @pr_child)

  else if (@pr_child_level = 3)
    set @p_parent = (select top 1 [Hierarchy One -2] from dbo.OPG011_eventData  with (nolock) where [Hierarchy One -3] = @pr_child)

  else if (@pr_child_level = 2)
    set @p_parent = (select top 1 [Hierarchy One -1] from dbo.OPG011_eventData  with (nolock) where [Hierarchy One -2] = @pr_child)

  else if (@pr_child_level = 1)
    set @p_parent = (select top 1 [Hierarchy One Top] from dbo.OPG011_eventData  with (nolock) where [Hierarchy One -1] = @pr_child)
  
  set @p_result_status = 'OK'
end


-- EOF