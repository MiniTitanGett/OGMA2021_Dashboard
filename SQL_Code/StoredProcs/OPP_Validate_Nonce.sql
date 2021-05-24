if exists (select * from sysobjects where [name] = 'OPP_Validate_Nonce') drop procedure dbo.OPP_Validate_Nonce 
go

-- Copyright © OGMA Consulting Corp.
-- $Id: 52be3a5dda04585d0bd16c4f5729c2e8e248ddd2 $
Create Procedure dbo.OPP_Validate_Nonce

--i Purpose: Validate a NONCE for use with the Dash graphical objects. 
--i
--i          Date              By       Event #  Parms Changed Y/N  Description of change
--    -----------------  -------------  -------  -----------------  ------------------------------------------------------------------------
--ic  2020/05/31  14:53  Mike Gruber    12844    N                  Created stored procedure.

@pr_session_id     int, 
@pr_nonce_key      varchar(64),
@pr_nonce_value    varchar(max),
@p_external_id     int           output,
@p_result_status   varchar(255)  output
 
as
begin
  set nocount on

  set @p_result_status = 'NoOK'

  declare @errPref varchar(64)
  set @errPref = 'SQOPPValidateNonce'
  
  if (isnull(@pr_session_id, 0) = 0)
  begin
    set @p_result_status = @errPref + '001|session_id is required.' 
    return
  end

  set @p_external_id = 123456789
  set @p_result_status = 'OK' 
end