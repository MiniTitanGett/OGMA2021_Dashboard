if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[OPP_Get_Hierarchy]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[OPP_Get_Hierarchy_Parent]
go

-- Copyright � OGMA Consulting Corp.
-- $Id$
Create Procedure dbo.OPP_Get_Hierarchy

@pr_session_id   int,
@pr_language     varchar(20),
@pr_child        varchar(64),
@p_result_status varchar(255) output


as
begin
  set nocount on

  set @p_result_status = 'NoOK'


  if (@pr_child = 'H0')
    select distinct [Hierarchy1]  as [result] from dbo.OrgHierarchy where ltrim(rtrim(isnull([Hierarchy1], ''))) <> ''
  else if (@pr_child = 'H1')
    select distinct [Hierarchy2]  as [result] from dbo.OrgHierarchy where ltrim(rtrim(isnull([Hierarchy2], ''))) <> ''
  else if (@pr_child = 'H2')
    select distinct [Hierarchy3]  as [result] from dbo.OrgHierarchy where ltrim(rtrim(isnull([Hierarchy3], ''))) <> ''
  else if (@pr_child = 'H3')
    select distinct [Hierarchy4]  as [result] from dbo.OrgHierarchy where ltrim(rtrim(isnull([Hierarchy4], ''))) <> '';
  else if (@pr_child = 'H4')
    select distinct [Hierarchy5]  as [result] from dbo.OrgHierarchy where  ltrim(rtrim(isnull([Hierarchy5], ''))) <> '';
  else
    select distinct [HierarchyLeaf] as [result] from dbo.OrgHierarchy where ltrim(rtrim(isnull([HierarchyLeaf], ''))) <> '';


  set @p_result_status = 'OK'
end


-- EOF