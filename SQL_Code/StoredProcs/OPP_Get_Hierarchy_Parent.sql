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
@p_result_status varchar(255) output,
@p_child_value   int output

as
begin
  set nocount on

  set @p_result_status = 'NoOK'

  set @p_parent = @pr_child

  while ((@p_parent is not null) and (@p_parent = @pr_child))
  begin

    if (@pr_child_level = 5)
      set @p_parent = (select top 1 [Hierarchy5] from dbo.OPG011_eventData with (nolock) where [HierarchyLeaf] = @pr_child)

    else if (@pr_child_level = 4)
      set @p_parent = (select top 1 [Hierarchy4] from dbo.OPG011_eventData with (nolock) where [Hierarchy5] = @pr_child)

    else if (@pr_child_level = 3)
      set @p_parent = (select top 1 [Hierarchy3] from dbo.OPG011_eventData with (nolock) where [Hierarchy4] = @pr_child)

    else if (@pr_child_level = 2)
      set @p_parent = (select top 1 [Hierarchy2] from dbo.OPG011_eventData with (nolock) where [Hierarchy3] = @pr_child)

    else if (@pr_child_level = 1)
      set @p_parent = (select top 1 [Hierarchy1] from dbo.OPG011_eventData with (nolock) where [Hierarchy2] = @pr_child)

    if (@pr_child_level = 0)
      set @p_parent = null

    if (@p_parent = @pr_child)
      set @pr_child_level = @pr_child_level - 1

  end
  set @p_child_value  = @pr_child_level
  set @p_result_status = 'OK'
end


-- EOF