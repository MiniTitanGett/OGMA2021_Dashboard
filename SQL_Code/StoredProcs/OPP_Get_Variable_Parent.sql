if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[OPP_Get_Variable_Parent]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[OPP_Get_Variable_Parent]
go

-- Copyright � OGMA Consulting Corp.
-- $Id$
Create Procedure dbo.OPP_Get_Variable_Parent

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

  if (@pr_child_level = 2)
    set @p_parent = (select top 1 [Variable Name Qualifier] from dbo.OPG001 with (nolock) where [Variable Name Sub Qualifier] = @pr_child)

  else if (@pr_child_level = 1)
    set @p_parent = (select top 1 [Variable Name] from dbo.OPG001 with (nolock) where [Variable Name Qualifier] = @pr_child)
  
  set @p_result_status = 'OK'
end


-- EOF