if exists (select * from sysobjects where [name] = 'OPP_AddGetEditDeleteFind_ExtDashboards') drop procedure dbo.OPP_AddGetEditDeleteFind_ExtDashboards
go

-- Copyright © OGMA Consulting Corp.
-- $Id$
Create Procedure dbo.OPP_AddGetEditDeleteFind_ExtDashboards

----i Purpose: Add/Get/Edit/Delete/Find External Dashboards.
----i
----i          Date              By       Event #  Parms Changed Y/N  Description of change
----    -----------------  -------------  -------  -----------------  -----------------------------------
----ic  2020/08/12  11:50  Mike Gruber    12808    N                  Created stored procedure.

@pr_session_id      int, 
@pr_action          varchar(64),          -- Add|Get|Edit|Delete|Find
@pr_dashboard_name  varchar(64),          -- ex. 'Dashboard_Ext_MyNewDashboard' required on Add/Get/Edit/Delete
@p_dashboard_title  varchar(255),         -- ex. 'My New Dashboard' required on Add
@p_dashboard_type   varchar(64),          -- ex. 'Dash' required on Add
@p_dashboard_layout varchar(max),         -- required on Add/Edit
@p_layout_type      varchar(64),          -- ex. 'application/json', content type of layout file; required on Add
@p_layout_ext       varchar(6),           -- ex. 'json', layout filename extension; required on Add
@p_result_status    varchar(255)  output
 
as
begin
  set nocount on

  set @p_result_status = 'NoOK'

  declare @errPref varchar(64)
  set @errPref = 'SQOPPAddGetEditDeleteFindExtDashboards'

  declare @sysPoptId int
  set @sysPoptId = 1

  declare @t_ref_id int
  declare @t_ref_value varchar(64)
  declare @t_ref_desc varchar(255)
  --declare @t_dashboard_ref varchar(64)
  --declare @t_dashboard_char varchar(64)
  declare @t_dashboard_desc varchar(255)
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

  if ((isnull(@pr_dashboard_name, '') = '') and (@pr_action <> 'Find'))
  begin
    set @p_result_status = @errPref + '002|dashboard_name is required.'
    return
  end

  --set @t_dashboard_ref = 'Dashboard_Ext_' + replace(@pr_dashboard_name, ' ', '')
  --set @t_dashboard_char = @t_dashboard_ref + 'Char'

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

    if (isnull(@p_dashboard_title, '') = '')
    begin
      set @p_result_status = @errPref + '030|dashboard_title is required with an action of Add or Edit.'
      return
    end

    if (isnull(@p_dashboard_type, '') = '')
    begin
      set @p_result_status = @errPref + '003|dashboard_type is required with an action of Add.'
      return
    end

    if (isnull(@p_dashboard_layout, '') = '')
    begin
      set @p_result_status = @errPref + '004|dashboard_layout is required with an action of Add or Edit.'
      return
    end

    if (isnull(@p_layout_type, '') = '')
    begin
      set @p_result_status = @errPref + '013|layout_type is required with an action of Add.'
      return
    end

    if (isnull(@p_layout_ext, '') = '')
    begin
      set @p_result_status = @errPref + '014|layout_ext is required with an action of Add.'
      return
    end

    --
    -- check for a unique dashboard ref entry
    --
    if (exists (select top 1 1
                  from dbo.op_ref with (nolock)
                 where ref_table = 'ExtDashboards'
                   and ref_value = @pr_dashboard_name))
    begin
      set @p_result_status = @errPref + '022|Dashboard already exists.'
      return
    end

    --
    -- add the ext dashboard ref entry
    --
    insert dbo.op_ref (ref_table, ref_value, [language], ref_desc)
    values ('ExtDashboards', @pr_dashboard_name, 'En', @p_dashboard_title)

    --
    -- add the layoutFile ref entry
    --
    insert dbo.op_ref (ref_table, ref_value, [language], ref_desc)
    values (@pr_dashboard_name, 'layoutFile', 'En', @pr_dashboard_name)

    --
    -- add the layoutFile char
    insert dbo.op_char (person_id, char_type, char_type_qualifier, char_value_text)
    values (@t_popt_id, @pr_dashboard_name, 'layoutFile', @p_dashboard_layout)

  end

  --
  -- Get
  --
  else if (@pr_action = 'Get')
  begin

    select cha.char_id,
           @pr_dashboard_name + '.json' as clob_filename,
           'application/json',  --'Dash',
           cha.char_value_text as clob_text,
           len(cha.char_value_text) as clob_size,
           ref.ref_desc
      from dbo.op_char as cha with (nolock)
     inner join dbo.op_ref as ref with (nolock)
        on ref_table = 'ExtDashboards'
       and ref_value = @pr_dashboard_name
       and [language] = 'En'
     where cha.person_id = @t_popt_id
       and cha.char_type = @pr_dashboard_name
       and cha.char_type_qualifier = 'layoutFile'

  end

  --
  -- Edit
  --
  else if (@pr_action = 'Edit')
  begin

    if (isnull(@p_dashboard_layout, '') = '')
    begin
      set @p_result_status = @errPref + '004|dashboard_layout is required with an action of Add or Edit.'
      return
    end

    set @t_char_id = null
    set @t_char_id = (select char_id
                        from dbo.op_char with (nolock)
                       where person_id = @t_popt_id
                         and char_type = @pr_dashboard_name
                         and char_type_qualifier = 'layoutFile')

    if (@t_char_id is null)
    begin
      set @p_result_status = @errPref + '016|dashboard layout not found.'
      return
    end

    update dbo.op_char
       set char_value_text = @p_dashboard_layout
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

    --
    -- check if the dashboard exists in ref
    --
    if (not exists (select top 1 1
                      from dbo.op_ref with (nolock)
                     where ref_table = 'ExtDashboards'
                       and ref_value = @pr_dashboard_name))
    begin
      set @p_result_status = @errPref + '023|Dashboard does not exist.'
      return
    end

    --
    -- delete the layoutFile char
    --
    delete dbo.op_char
     where person_id = @t_popt_id
       and char_type = @pr_dashboard_name
       and char_type_qualifier = 'layoutFile'

    --
    -- delete the layoutFile ref entry
    --
    delete dbo.op_ref
     where ref_table = @pr_dashboard_name
       and ref_value = 'layoutFile'

    --
    -- add the ext dashboard ref entry
    --
    delete dbo.op_ref
     where ref_table = 'ExtDashboards'
       and ref_value = @pr_dashboard_name

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
           ref.ref_table + '.json',
           'application/json',
           cha.char_value_text,
           len(cha.char_value_text)
      from dbo.op_ref as ref with (nolock)
     inner join dbo.op_char as cha with (nolock)
        on cha.person_id = @t_popt_id
       and cha.char_type = ref.ref_value
       and cha.char_type_qualifier = 'layoutFile'
     where ref.ref_table = 'ExtDashboards'
       and [language] = 'En'

    select *
      from @t_results
     order by ref_desc

  end

  set @p_result_status = 'OK'
end


-- EOF