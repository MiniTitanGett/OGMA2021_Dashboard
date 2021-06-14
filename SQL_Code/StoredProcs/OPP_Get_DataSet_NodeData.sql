if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[OPP_Get_DataSet_NodeData]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[OPP_Get_DataSet_NodeData]
go

-- Copyright © OGMA Consulting Corp.
-- $Id$
Create Procedure dbo.OPP_Get_DataSet_NodeData

@pr_session_id    int,
@pr_language      varchar(20),
@pr_dataset_name  varchar(64),        
@p_result_status  varchar (255) output

as
begin
  set nocount on

  set @p_result_status = 'NoOK'

  set @pr_dataset_name = isnull(@pr_dataset_name, 'NOTSET')

  if (@pr_dataset_name = 'OPG010')
    select * from dbo.OPG010_NodeData

  else
  begin
    set @p_result_status = 'OPP_Get_Dataset_NodeData001|Dataset does not have associated node data:' + @pr_dataset_name
    return
  end
  
  set @p_result_status = 'OK'
end


-- EOF