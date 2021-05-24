if exists (select * from dbo.sysobjects where id = object_id(N'[dbo].[OPP_Get_Session2]') and OBJECTPROPERTY(id, N'IsProcedure') = 1)
drop procedure [dbo].[OPP_Get_Session2]
go

-- Copyright © OGMA Consulting Corp.
-- $Id: 241ff5aad9f2ba161d1e65c2c4d4215b9774c65b $
Create Procedure dbo.OPP_Get_Session2
---i Purpose:  obtain current session info for a login and mark last access date.
----i    Date              By                Event #   Parms Changed Y/N  Description of change
----     ----------        -----------------------------   ------------   ---------------------------------
----ic  2001/05/18  11:02  Michael            none            N            created to replace opp_Get_Sessions
----ic  2001/06/06  13:45  Michael            none            N            check for session status
----ic  2001/07/30  13:43  Janice             none            N            print timeout messages in current_lang
----ic  2002/01/02  12:02  Stan               none            N            last access date was declared as varchar(20) but casted to 16
----ic  2002/02/19  12:43  Alexis             none            N            changed retrieval for timeout message - it's now a characteristic
----ic  2002/02/20  09:23  Alexis             none            N            changed retrieval for user logged off message - it's now a characteristic
----ic  2002/02/27  13:52  Ping               none            N            Fix time out message
----ic  2002/03/08  08:55  Janice             none            N            Send back a default timeout msg for use by Delphi
----ic  2002/03/07  13:15  Janice             3115            N            Added 'read_only's.
----ic  2002/04/24  13:15  Alan               3115            Y            added Current_org_id
----ic  2002/04/26  16:55  Alexis             3115            Y--output    added @p_logout_message, @p_logout_alt
----ic  2002/05/01  10:42  Mike Gruber        3115            Y            changed @p_logout_alt to @p_logout_text
----ic  2002/06/05  12:23  MIke Gruber        3115            Y            added @p_is_super_user
----ic  2002/07/12  08:15  Mike Gruber        3115            N            Explicitly checking for session record on file (returns 'NoRecord' if not exists)
----ic  2002/07/29  16:40  Janice             3115            Y            added @Doc_Lang
----ic  2002/08/21  10:40  Michael            3115            N            applied speed enhancements from v214d5a
----ic  2003/09/22  14:01  Alan               1515            Y            Added @p_default_printer - StyleReports printer
----ic  2004/03/01  13:35  Stan               1962            N            Removed Timeout+1day, etc; only using time characteristic
----ic  2005/01/15  13:52  Mike Gruber        2666            N            Removed sensitive system information from session timeout message.
----ic  2010/03/11  15:35  Stan               6231            N            Added provision for Last_Access_Date
----ic  2010/04/27  15:20  Stan               6362            N            Make sure @pr_sys_popt_id is not null
----ic  2011/07/18  13:52  Mike Gruber        8070            Y            Added 'TokenID' parameter.
----ic  2014/10/02  11:46  Janice             10485           Y            Added DefaultSearchTerm param
----ic  2015/06/08  16:20  Stan               10823           N            Moved the language defaulting of @Current_Lang earlier in the routine; before the 1st use of the variable
----ic  2018/03/06  13:52  Mike Gruber        12148           Y            Added @p_csrf_token_name, @p_csrf_token_value params.
----ic  2020/06/03  13:52  Mike Gruber        12844           Y            Added @p_external_id param.

@pr_Session_id                   int,     -- The session id running the
@pr_Session_id2                  int,     -- The session id for the query
@pr_sys_popt_id                  int,
@TokenID                         int          output,
@Logon_POPT_Id                   varchar(16)  output,
@POPT_Id_I                       varchar(16)  output,
@Current_Org_Id                  varchar(16)  output,
@Last_Access_Dt                  varchar(20)  output,
@Current_Lang                    varchar(64)  output,
@Doc_Lang                        varchar(20)  output,
@Current_User_Class_Seq          varchar(16)  output,
@Current_User_Pop_Type_Qualifier varchar(64)  output,
@Currently_Personalized_B        varchar(01)  output,
@Current_Date_Format             varchar(64)  output,
@Current_Numeric_Format          varchar(64)  output,
@Current_Monetary_Format         varchar(64)  output,
@Access_Method                   varchar(20)  output,
@Logon_Domain                    varchar(10)  output,
@p_mark_accessed                 varchar(1),
@p_Session_Status                varchar(64)  output,
@p_timeout_message               varchar(255) output,
@p_logout_message                varchar(255) output,
@p_logout_text                   varchar(255) output,
@p_is_super_user                 char(1)      output,
@p_default_printer               varchar(64)  output,
@DefaultSearchTerm               varchar(64)  output,
@p_csrf_token_name               varchar(64)  output,  -- #12148
@p_csrf_token_value              varchar(256) output,  -- #12148
@p_external_id                   int          output,
@p_result_status                 varchar(255) output

as
begin
  set nocount on
  --
  if @pr_sys_popt_id is null set @pr_sys_popt_id = 1
  --
  set @P_Session_Status = null
  set @p_timeout_message = ' '

  declare @t_timeout_minutes_str varchar (64)
  declare @t_timeout_minutes     int
  declare @t_now           datetime
  declare @t_last          datetime
  declare @session_status  varchar (20)
  declare @t_elapsed_time  int

  set @t_now = getdate()

  select
    @POPT_Id_I = cast(person_id as varchar (16))
    from dbo.op_Curr_Sessions with (nolock)
    where session_id = @pr_Session_Id2

  if @@rowcount = 1
    set @p_result_status = 'OK'
  else
  begin
    set @p_session_status = 'NoRecord'
    set @p_result_status  = 'NoRecord'
    return
  end

  set @p_external_id = 123456789
  set @p_session_status = 'OK'
  set @p_result_status = 'OK'
end
