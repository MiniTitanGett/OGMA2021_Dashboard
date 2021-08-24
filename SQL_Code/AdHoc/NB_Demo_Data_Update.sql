-- secript to change the data for NB

update dbo.opg001
   set [Activity Event Id] = '14968163'

update dbo.opg001C
   set [Activity Event Id] = '14968163'

update dbo.OPG010
   set [Activity Event Id] = '14968163'

update dbo.opg001
   set [Variable Name] = case
                           when [Variable Name] = 'Bid' then 'Tender'
                           when [Variable Name] = 'SPO' then 'Release'
                           else [Variable Name]
                         end,
       [Variable Name Qualifier] = replace(replace(replace(replace([Variable Name Qualifier], 'Bid ', 'Tender '), ' Bid', ' Tender'), 'SPO ', 'Release '), ' SPO', ' Release')

update dbo.opg001c
   set [Variable Name] = case
                           when [Variable Name] = 'Bid' then 'Tender'
                           when [Variable Name] = 'SPO' then 'Release'
                           else [Variable Name]
                         end,
       [Variable Name Qualifier] = replace(replace(replace(replace([Variable Name Qualifier], 'Bid ', 'Tender '), ' Bid', ' Tender'), 'SPO ', 'Release '), ' SPO', ' Release')


delete dbo.op_ref
 where ref_table = 'Data_set'
   and ref_value = 'OPG011'

update dbo.opg001
   set [Hierarchy One Top] = 'NBON-RPANB'
 where [Hierarchy One Top] = 'Los Angeles Department of Water and Power'

update dbo.opg001
   set [Hierarchy One -1] = 'SUPPORT SERVICES'
 where [Hierarchy One -1] = 'DEPARTMENT SUPPT SVCS'

update dbo.opg001
   set [Hierarchy One -1] = 'HEALTH AUTHORITIES'
 where [Hierarchy One -1] = 'IPRP Data Conversion Orgs'

 update dbo.opg001
   set [Hierarchy One -1] = 'MARKETING SERVICES'
 where [Hierarchy One -1] = 'MARKETING & CUSTOMER SVC'

update dbo.opg001
   set [Hierarchy One -1] = 'HEALTH AUTHORITIES'
 where [Hierarchy One -1] = 'IPRP Data Conversion Orgs'

 update dbo.opg001
   set [Hierarchy One -1] = 'SCHEDULE A'
 where [Hierarchy One -1] = 'POWER SERVICES'

 update dbo.opg001
   set [Hierarchy One -1] = 'SCHEDULE B'
 where [Hierarchy One -1] = 'WATER SYSTEM'

 update dbo.opg001
   set [Hierarchy One -1] = 'GNB PROCUREMENT'
 where [Hierarchy One -1] = 'PURCHASING - BUYER PARENT ORG'

 update dbo.opg001
    set [Hierarchy One -2] = 'FUEL PURCHASE DIVISION'
  where [Hierarchy One -2] = 'PWR AND FUEL PURCHASE DIV'

 update dbo.opg001
    set [Hierarchy One -2] = replace(replace(replace(replace([Hierarchy One -2], 'POWER ', 'SCHEDULE A '), ' POWER', ' SCHEDULE A'), 'WATER ', 'SCHEDULE B '), ' WATER', ' SCHEDULE B')

 update dbo.opg001
    set [Hierarchy One -3] = replace(replace(replace(replace([Hierarchy One -3], 'POWER ', 'SCHEDULE A '), ' POWER', ' SCHEDULE A'), 'WATER ', 'SCHEDULE B '), ' WATER', ' SCHEDULE B')

 update dbo.opg001
    set [Hierarchy One -4] = replace(replace(replace(replace([Hierarchy One -4], 'POWER ', 'SCHEDULE A '), ' POWER', ' SCHEDULE A'), 'WATER ', 'SCHEDULE B '), ' WATER', ' SCHEDULE B')

 update dbo.opg001
    set [Hierarchy One Leaf] = replace(replace(replace(replace([Hierarchy One Leaf], 'POWER ', 'SCHEDULE A '), ' POWER', ' SCHEDULE A'), 'WATER ', 'SCHEDULE B '), ' WATER', ' SCHEDULE B')

update dbo.opg010
   set [Hierarchy One Top] = 'NBON-RPANB'
 where [Hierarchy One Top] = 'Los Angeles Department of Water and Power'


-- EOF