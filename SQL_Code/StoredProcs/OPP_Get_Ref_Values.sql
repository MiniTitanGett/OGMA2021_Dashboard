if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[spOPref_getOPrefdata]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[spOPref_getOPrefdata]
go

if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[OPP_Get_Ref_Values]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[OPP_Get_Ref_Values]
go

-- Copyright © OGMA Consulting Corp.
-- $Id$
Create Procedure dbo.OPP_Get_Ref_Values
----i Purpose:  Return a list of table values, excluding values passed
----i          Date              By       Event #  Parms Changed Y/N  Description of change
----    -----------------  -------------  -------  -----------------  ------------------------------------------------------------------------
----ic  2001/07/30  15:00  Celia          3115     N                  New routine to return reference values as a result set
----ic  2002/03/26  10:39  Angela         3115     N                  ordered the result set by ref_seq
----ic  2003/04/22  09:08  Angela         1005     N                  modified to return only active values
----ic  2004/11/05  14:00  Stan           2591     N                  Optimized routine (deleted call to OPP_Exclude_Values...use logic in this routine)
----ic  2005/05/16  12:14  Mike Gruber    2869     N                  Added ref_seq to result set.
----ic  2005/05/20  14:44  Mike Gruber    2869     N                  Added ref_info to result set.
----ic  2006/10/24  14:55  Angela Gruber  3897     N                  Added Ref_LinkValue to result set.
----ic  2009/09/17  11:13  Mike Gruber    5966     N                  Added linktype, ref_datatype to result set.
----ic  2009/10/19  14:54  Angela Gruber  6028     N                  Added Ref_Optionality
----ic  2010/06/23  09:19  Angela Gruber  6536     N                  Added Ref_HTML_Misc
----ic  2011/12/06  14:55  Angela Gruber  8548     N                  Added Ref_JS_Edit
----ic  2011/12/13  11:55  Angela Gruber  8548     N                  Added Ref_HTML_Present
----ic  2014/12/15  18:24  Alexis         10550    Y                  added p_sort_by, fiddle exclude

@pr_session_id    int,                  -- Required
@p_ref_table      varchar(64),
@p_language       varchar(20),
@p_exclude        varchar(2048),        -- values to exclude eg: 'value1||value2||'
@p_sort_by        varchar(4),           -- 'Desc', 'Seq' (default)
@p_result_status  varchar (255) output

as
begin
  set nocount on

  set @p_result_status = 'NoOK'
  
  declare @t_exclude varchar(2050)
  set @t_exclude = '||' + @p_exclude -- this ensures that 'BigBob' in the exclude does not match 'Bob' in the ref_value
  
  if (@t_exclude is null)
    set @t_exclude = '' -- do not want to check for null
	
  if (isnull(@p_sort_by, '') = '')
    set @p_sort_by = 'Seq'

  select ref_value,
         ref_desc,
		 null as ref_info,
		 1 as ref_seq,
		 null as linktype,
		 null as ref_linkvalue,
		 null as ref_datatype,
		 null as ref_optionality,
		 null as ref_html_misc,
		 null as ref_js_edit,
		 null as ref_html_present
	from dbo.op_ref with (nolock)
   where ref_table = @p_ref_table
     and [language] = @p_language
	 and ((@t_exclude = '') or (@t_exclude not like '%||' + ref_value + '||%'))
   order by case when @p_sort_by = 'Desc' then ref_desc end, ref_value
  
  set @p_result_status = 'OK'
end
