"""Unit-safe candidate grids; the legacy spatial pipeline remains unchanged.

Grid cell side length is 3,000 metres. EPSG:32118 uses metres and the same
NAD83 / New York Long Island projection family as legacy EPSG:2263.
"""
from dataclasses import dataclass
import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import CRS
from shapely.geometry import box

GRID_CELL_SIZE_METERS = 3000
CONSTRUCTION_CRS = 'EPSG:32118'
GEOMETRY_TOLERANCE_METERS = 1e-6
DIRECTIONS = {'cardinal': [('N', -1, 0), ('E', 0, 1), ('S', 1, 0), ('W', 0, -1)],
              '8way': [('N', -1, 0), ('NE', -1, 1), ('E', 0, 1), ('SE', 1, 1),
                       ('S', 1, 0), ('SW', 1, -1), ('W', 0, -1), ('NW', -1, -1)]}

@dataclass
class MetricGridResult:
    grid: gpd.GeoDataFrame
    zone_mapping: pd.DataFrame
    raster: pd.DataFrame
    generated_cells: int
    rows: int
    columns: int
    boundary_bounds: list


def _require_metres(crs):
    c = CRS.from_user_input(crs)
    if not c.is_projected or len(c.axis_info) < 2 or any(
        not np.isclose(a.unit_conversion_factor, 1., rtol=0, atol=1e-12)
        for a in c.axis_info[:2]
    ):
        raise ValueError('Construction/output CRS must be projected in metres.')


def build_metric_grid(zones: gpd.GeoDataFrame, *, construction_crs=CONSTRUCTION_CRS):
    """Grid cell side length is 3,000 metres.

    Project the unchanged boundary, create full squares anchored at its lower
    bounds, retain polygon intersections like the legacy overlay, and order IDs
    north-to-south/west-to-east. Full lattice indices preserve empty rows/columns.
    This API deliberately does not read the legacy feet-labelled size config.
    """
    _require_metres(construction_crs)
    if zones.crs is None or 'LocationID' not in zones or zones.empty:
        raise ValueError('Nonempty georeferenced taxi zones with LocationID required.')
    if zones.geometry.isna().any() or (~zones.geometry.is_valid).any():
        raise ValueError('Invalid source geometry; do not silently repair study area.')
    z = zones.to_crs(construction_crs)
    xmin, ymin, xmax, ymax = z.total_bounds
    side = GRID_CELL_SIZE_METERS
    cols, rows = int(np.ceil((xmax-xmin)/side)), int(np.ceil((ymax-ymin)/side))
    records = [(r, c, box(xmin+c*side, ymin+(rows-r-1)*side,
                          xmin+(c+1)*side, ymin+(rows-r)*side))
               for r in range(rows) for c in range(cols)]
    full = gpd.GeoDataFrame(records, columns=['Row','Column','geometry'], crs=z.crs)
    full['LatticeID'] = np.arange(len(full))
    # Same polygon-only intersection inclusion as gpd.overlay's legacy default.
    overlap = gpd.overlay(full[['LatticeID','geometry']], z[['LocationID','geometry']],
                          how='intersection', keep_geom_type=True)
    if overlap.empty:
        raise ValueError('No polygon intersections with source boundary.')
    grid = full[full.LatticeID.isin(overlap.LatticeID)].copy().reset_index(drop=True)
    grid['GridID'] = np.arange(len(grid), dtype=np.int32)
    grid['CentroidX'] = grid.geometry.centroid.x
    grid['CentroidY'] = grid.geometry.centroid.y
    grid['ValidMask'] = True
    lookup = dict(zip(grid.LatticeID, grid.GridID))
    mapping = overlap[['LocationID','LatticeID']].drop_duplicates().copy()
    mapping['GridID'] = mapping.LatticeID.map(lookup)
    mapping = mapping[['LocationID','GridID']].sort_values(['LocationID','GridID']).reset_index(drop=True)
    raster = full[['LatticeID','Row','Column']].copy()
    raster['GridID'] = raster.LatticeID.map(lookup).astype('Int64')
    raster['ValidMask'] = raster.GridID.notna()
    validate_metric_grid(grid)
    return MetricGridResult(grid, mapping, raster, rows*cols, rows, cols, z.total_bounds.tolist())


def validate_metric_grid(grid, tolerance=GEOMETRY_TOLERANCE_METERS):
    """Measure saved polygons, not metadata labels; reject non-square/incorrect cells."""
    _require_metres(grid.crs)
    if grid.empty or not grid.GridID.is_unique or grid[['Row','Column']].duplicated().any():
        raise ValueError('Invalid or duplicate grid identity/raster mapping.')
    if not np.array_equal(grid.GridID.to_numpy(), np.arange(len(grid))):
        raise ValueError('GridIDs must follow deterministic raster order.')
    if list(zip(grid.Row,grid.Column)) != sorted(zip(grid.Row,grid.Column)):
        raise ValueError('GridID order must be north-to-south, west-to-east.')
    b = grid.geometry.bounds
    widths, heights = b.maxx-b.minx, b.maxy-b.miny
    if not np.allclose(widths,3000,rtol=0,atol=tolerance) or not np.allclose(heights,3000,rtol=0,atol=tolerance):
        raise ValueError('Geometry dimensions must be 3000 metres.')
    for geom, bounds in zip(grid.geometry,b.to_numpy()):
        if not geom.is_valid or geom.symmetric_difference(box(*bounds)).area > tolerance:
            raise ValueError('Cell must be a full axis-aligned square.')
    centroids=grid.geometry.centroid
    if not np.allclose(centroids.x,grid.CentroidX,rtol=0,atol=tolerance) or not np.allclose(centroids.y,grid.CentroidY,rtol=0,atol=tolerance):
        raise ValueError('Stored centroid does not match polygon.')
    return {'width_min_m':float(widths.min()),'width_max_m':float(widths.max()),
            'height_min_m':float(heights.min()),'height_max_m':float(heights.max()),
            'area_min_km2':float(grid.area.min()/1e6),'area_max_km2':float(grid.area.max()/1e6),
            'tolerance_m':tolerance}


def build_metric_neighbors(grid, topology):
    """Directed valid-cell links; STAY index0 is implicit, never an edge.

    Eight-way indices1..8 follow N,NE,E,SE,S,SW,W,NW. Diagonals require a
    valid destination only; no road or water-crossing feasibility is implied.
    """
    validate_metric_grid(grid)
    directions=DIRECTIONS[topology]
    positions={(int(r.Row),int(r.Column)):int(r.GridID) for r in grid.itertuples()}
    coords=grid.set_index('GridID')[['CentroidX','CentroidY']]
    links=[]
    for r in grid.itertuples():
        for index,(direction,dr,dc) in enumerate(directions,1):
            other=positions.get((int(r.Row)+dr,int(r.Column)+dc))
            if other is None:continue
            distance=float(np.linalg.norm(coords.loc[other].to_numpy()-coords.loc[r.GridID].to_numpy()))
            expected=3000*np.hypot(dr,dc)
            if not np.isclose(distance,expected,rtol=0,atol=GEOMETRY_TOLERANCE_METERS):
                raise ValueError('Raster neighbour spacing disagrees with geometry.')
            links.append((int(r.GridID),other,direction,index,distance))
    return pd.DataFrame(links,columns=['GridID','NeighbourGridID','Direction','ActionIndex','DistanceMeters'])


def topology_summary(grid, links, topology):
    counts=links.groupby('GridID').size().reindex(grid.GridID,fill_value=0)
    adjacency={int(i):set() for i in grid.GridID}
    for r in links.itertuples():adjacency[r.GridID].add(r.NeighbourGridID)
    remaining=set(adjacency);components=[]
    while remaining:
        stack=[min(remaining)];remaining.remove(stack[0]);size=0
        while stack:
            u=stack.pop();size+=1
            for v in adjacency[u]&remaining:remaining.remove(v);stack.append(v)
        components.append(size)
    return {'directed_links':len(links),'mean_neighbors':float(counts.mean()),
            'min_neighbors':int(counts.min()),'max_neighbors':int(counts.max()),
            'boundary_grids':int((counts<len(DIRECTIONS[topology])).sum()),
            'isolated_grids':counts[counts==0].index.astype(int).tolist(),
            'connected_component_sizes':sorted(components,reverse=True)}
