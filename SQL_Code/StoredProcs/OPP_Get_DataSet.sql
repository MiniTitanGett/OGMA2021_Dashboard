if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[OPP_Get_DataSet]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[OPP_Get_DataSet]
go

-- Copyright © OGMA Consulting Corp.
-- $Id$
Create Procedure dbo.OPP_Get_DataSet

@pr_session_id    int,
@pr_language      varchar(20),
@pr_dataset_name  varchar(64),        
@p_result_status  varchar (255) output

as
begin
  set nocount on

  set @p_result_status = 'NoOK'

  set @pr_dataset_name = isnull(@pr_dataset_name, 'NOTSET')

  if (@pr_dataset_name = 'OPG001')
    select * from dbo.OPG001
  
  else if (@pr_dataset_name = 'OPG010')
    select * from dbo.OPG010

  else if (@pr_dataset_name = 'OPG011')
    select --null [OPG Data Set],
           --null [Hierarchy One Name],
           --null [Hierarchy One Top],
           --null [Hierarchy One -1],
           --null [Hierarchy One -2],
           --null [Hierarchy One -3],
           --null [Hierarchy One -4],
           [Hierarchy One Leaf] as [Hierarchy Value],
           5 as [Hierarchy Level],
           [Variable Name],
           [Variable Name Qualifier],
           [Variable Name Sub Qualifier],
           case
             when isnull([Variable Name Sub Qualifier], '') <> '' then [Variable Name Sub Qualifier]
             else [Variable Name Qualifier]
           end as [Variable Name Value],
           case
             when isnull([Variable Name Sub Qualifier], '') <> '' then 3
             else 2
           end as [Variable Level],
           [Date of Event],
           [Calendar Entry Type],
           --null [Year of Event],
           --null [Quarter],
           --null [Month of Event],
           --null [Week of Event],
           --null [Fiscal Year of Event],
           --null [Fiscal Quarter],
           --null [Fiscal Month of Event],
           --null [Fiscal Week of Event],
           --null [Julian Day],
           [Activity Event Id],
           [Measure Value],
           [Measure Type],
           [Partial Period]
      from dbo.OPG001 with (nolock)
     where trim(isnull([Hierarchy One Leaf], '')) <> ''
       -- we can't prune based on Sub Qualifier because the data is 'blown out',
       -- but since the data doesn't include any values in Sub Qualifier, we are ok
       and trim(isnull([Variable Name Qualifier], '')) <> ''
       and [Calendar Entry Type] = 'Week'

  else
  begin
    set @p_result_status = 'OPP_Get_Dataset001|Invalid dataset name: ' + @pr_dataset_name
    return
  end
  
  set @p_result_status = 'OK'
end


-- EOF