if exists (select * from sysobjects where [name] = 'OPP_AddGetEditDeleteFind_ExtDashboardReports') drop procedure dbo.OPP_AddGetEditDeleteFind_ExtDashboardReports
go

-- Copyright © OGMA Consulting Corp.
-- $Id: cda7f654ced3f78d13751a58a003e7e8f17cd53d $
Create Procedure dbo.OPP_AddGetEditDeleteFind_ExtDashboardReports

----i Purpose: Add/Get/Edit/Delete/Find External Dashboard Reports.
----i
----i          Date              By       Event #  Parms Changed Y/N  Description of change
----    -----------------  -------------  -------  -----------------  -----------------------------------
----ic  2020/08/12  11:50  Mike Gruber    12808    N                  Created stored procedure.

@pr_session_id     int, 
@pr_action         varchar(64),          -- Add|Get|Edit|Delete|Find
@pr_report_name    varchar(64),
@p_report_type     varchar(64),          -- ex. 'Dash' required on Add/Edit
@p_report_layout   varchar(max),         -- required on Add/Edit
@p_layout_type     varchar(64),          -- ex. 'application/json', content type of layout file; required on Add/Edit
@p_layout_ext      varchar(6),           -- ex. 'json', layout filename extension; required on Add/Edit
@p_result_status   varchar(255)  output
 
as
begin
  set nocount on

  set @p_result_status = 'NoOK'

  declare @errPref varchar(64)
  set @errPref = 'SQOPPAddGetEditDeleteFindExtDashboardReports'

  declare @sysPoptId int
  set @sysPoptId = 1

  declare @t_ref_id int
  declare @t_ref_value varchar(64)
  declare @t_ref_desc varchar(255)
  declare @t_report_ref varchar(64)
  declare @t_report_char varchar(64)
  declare @t_report_desc varchar(255)
  declare @t_parent_char_id int
  declare @t_char_id int
  declare @t_popt_id int
  declare @t_cursor cursor
  declare @t_cursor2 cursor

  if (isnull(@pr_action, '') not in ('Add', 'Get', 'Edit', 'Delete', 'Find'))
  begin
    set @p_result_status = @errPref + '001|action must be one of Add, Get, Edit, Delete, Find.'
    return
  end

  if ((isnull(@pr_report_name, '') = '') and (@pr_action <> 'Find'))
  begin
    set @p_result_status = @errPref + '002|report_name is required.'
    return
  end

  set @t_report_ref = 'Report_Ext_' + replace(@pr_report_name, ' ', '')
  set @t_report_char = @t_report_ref + 'Char'

  --
  -- get the person id from the session
  --
  set @t_popt_id = (select person_id
                      from dbo.op_curr_sessions with (nolock)
                     where session_id = @pr_session_id)

  --
  -- Add
  --
  if (@pr_action = 'Add')
  begin

    if (isnull(@p_report_type, '') = '')
    begin
      set @p_result_status = @errPref + '003|report_type is required with an action of Add or Edit.'
      return
    end

    if (isnull(@p_report_layout, '') = '')
    begin
      set @p_result_status = @errPref + '004|report_layout is required with an action of Add or Edit.'
      return
    end

    if (isnull(@p_layout_type, '') = '')
    begin
      set @p_result_status = @errPref + '013|layout_type is required with an action of Add or Edit.'
      return
    end

    if (isnull(@p_layout_ext, '') = '')
    begin
      set @p_result_status = @errPref + '014|layout_ext is required with an action of Add or Edit.'
      return
    end

    --
    -- check for a unique report ref entry
    --
    if (exists (select top 1 1
                  from dbo.op_ref with (nolock)
                 where ref_table = 'ExtDashboardReports'
                   and ref_value = @t_report_ref))
    begin
      set @p_result_status = @errPref + '022|Report already exists.'
      return
    end

    --
    -- add the ext report ref entry
    --
    insert dbo.op_ref (ref_table, ref_value, [language], ref_desc)
    values ('ExtDashboardReports', @t_report_ref, 'En', @pr_report_name)

    --
    -- add the layoutFile ref entry
    --
    insert dbo.op_ref (ref_table, ref_value, [language], ref_desc)
    values (@t_report_ref, 'layoutFile', 'En', @t_report_ref)

    --
    -- add the layoutFile char
    insert dbo.op_char (person_id, char_type, char_type_qualifier, char_value_text)
    values (@t_popt_id, @t_report_ref, 'layoutFile', @p_report_layout)

  end

  --
  -- Get
  --
  else if (@pr_action = 'Get')
  begin

    select cha.char_id,
           @pr_report_name + '[.]json' as clob_filename,
           'application/json',  --'Dash',
           cha.char_value_text as clob_text,
           len(cha.char_value_text) as clob_size,
           ref.ref_desc
      from dbo.op_char as cha with (nolock)
     inner join dbo.op_ref as ref with (nolock)
        on ref_table = 'ExtDashboardReports'
       and ref_value = @pr_report_name
       and [language] = 'En'
     where cha.person_id = @t_popt_id
       and cha.char_type = @pr_report_name
       and cha.char_type_qualifier = 'layoutFile'

  end

  --
  -- Edit
  --
  else if (@pr_action = 'Edit')
  begin

    if (isnull(@p_report_type, '') = '')
    begin
      set @p_result_status = @errPref + '003|report_type is required with an action of Add or Edit.'
      return
    end

    if (isnull(@p_report_layout, '') = '')
    begin
      set @p_result_status = @errPref + '004|report_layout is required with an action of Add or Edit.'
      return
    end

    if (isnull(@p_layout_type, '') = '')
    begin
      set @p_result_status = @errPref + '013|layout_type is required with an action of Add or Edit.'
      return
    end

    if (isnull(@p_layout_ext, '') = '')
    begin
      set @p_result_status = @errPref + '014|layout_ext is required with an action of Add or Edit.'
      return
    end

    set @t_char_id = null
    set @t_char_id = (select char_id
                        from dbo.op_char with (nolock)
                       where person_id = @t_popt_id
                         and char_type = @t_report_ref
                         and char_type_qualifier = 'layoutFile')

    if (@t_char_id is null)
    begin
      set @p_result_status = @errPref + '016|report not found.'
      return
    end

    update dbo.op_char
       set char_value_text = @p_report_layout
     where char_id = @t_char_id

  end

  --
  -- Delete
  --
  else if (@pr_action = 'Delete')
  begin

    -- CHECK SECURITY!!!

    -- CHECK IN-USE!!!

    -- for now, just super delete


    set @p_result_status = @errPref + '|Delete not currently available.'
    return
  end

  --
  -- Find
  --
  else if (@pr_action = 'Find')
  begin
    declare @t_results table (ref_value varchar(64), ref_desc varchar(255), char_id int,
        clob_filename varchar(64), clob_type varchar(64), clob_text varchar(max), clob_size int)

    insert @t_results (ref_value, ref_desc, char_id, clob_filename, clob_type, clob_text, clob_size)
    select ref.ref_value,
           ref.ref_desc,
           cha.char_id,
           ref.ref_table + '[.]json',
           'application/json',
           cha.char_value_text,
           len(cha.char_value_text)
      from dbo.op_ref as ref with (nolock)
     inner join dbo.op_char as cha with (nolock)
        on cha.person_id = @t_popt_id
       and cha.char_type = ref.ref_value
       and cha.char_type_qualifier = 'layoutFile'
     where ref.ref_table = 'ExtDashboardReports'
       and [language] = 'En'

    select *
      from @t_results
     order by ref_desc

  end

  set @p_result_status = 'OK'
end


-- EOF