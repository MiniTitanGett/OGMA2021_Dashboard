if exists (select * from sysobjects where [name] = 'OPP_OPG010_NodeData_Startup') drop procedure dbo.OPP_OPG010_NodeData_Startup 
go

create procedure dbo.OPP_OPG010_NodeData_Startup

@pr_node_id varchar(64),
@pr_x_coord numeric(4,3),
@pr_y_coord numeric(4,3),
@pr_colour  varchar(64)

as
begin
  set nocount on

  if (not exists (select top 1 1
                    from dbo.opg010_nodedata with (nolock)
                   where node_id = @pr_node_id))
    insert dbo.opg010_nodedata (node_id, x_coord, y_coord, colour)
    values (@pr_node_id, @pr_x_coord, @pr_y_coord, @pr_colour)
  else
    update dbo.opg010_nodedata
       set x_coord = @pr_x_coord,
           y_coord = @pr_y_coord,
           colour = @pr_colour
     where node_id = @pr_node_id

end
go

exec dbo.opp_opg010_nodedata_startup 'In6', 0.05, 0.05, 'rgba(230,38,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'In5', 0.1, 0.125, 'rgba(230,115,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'In4', 0.15, 0.25, 'rgba(230,191,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'In3', 0.2, 0.4, 'rgba(255,255,51,0.8)'
exec dbo.opp_opg010_nodedata_startup 'In2', 0.25, 0.575, 'rgba(191,230,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'In1', 0.3, 0.775, 'rgba(115,230,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'New', 0.35, 1, 'rgba(38,230,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'Out6', 0.85, 0.05, 'rgba(230,38,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'Out5', 0.8, 0.1, 'rgba(230,115,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'Out4', 0.75, 0.16, 'rgba(230,191,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'Out3', 0.7, 0.225, 'rgba(255,255,51,0.8)'
exec dbo.opp_opg010_nodedata_startup 'Out2', 0.65, 0.3, 'rgba(191,230,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'Out1', 0.6, 0.4, 'rgba(115,230,0,0.8)'
exec dbo.opp_opg010_nodedata_startup 'End', 0.55, 0.8, 'rgba(38,230,0,0.8)'

drop procedure dbo.OPP_OPG010_NodeData_Startup


-- EOF