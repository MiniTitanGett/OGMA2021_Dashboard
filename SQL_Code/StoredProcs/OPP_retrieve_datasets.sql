USE [OGMA_Test]
GO

if exists (select * from sysobjects where [name] = 'OPP_retrieve_datasets') drop procedure dbo.OPP_retrieve_datasets
go

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [dbo].[OPP_retrieve_datasets]
as
begin
    SELECT DISTINCT ref_value FROM [OGMA_Test].[dbo].[OP_Ref]
    WHERE ref_table='Data_set'
end
