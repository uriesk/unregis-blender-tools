##A script for Blender with lots of useful functions for creating meshes for SL or OpenSim

In SL one material is one "face" and one object can have 8 faces max. The less objects the better.

The link order is determinded by the order in the collada file (select "sort by object name" on collada export, or you will get a random order).

No no-gons allowed, Make sure the mesh consists only of tris and quads (to make sure of that, first convert the mesh to tris and then use the tris-to-quads function).

LOD models have to use the same amounts of materials as the original model.

When generating LODs by the Uploader, it will create degenerate triangles with 0 area for some materials that it would have removed otherwise.
This means that using the LOD model as physics model is discouraged, because degenerate triangles are bad for physics.

The Analyze button in the Physics tab, that is supposed to create a optimized convex shape out of the physics shape, generates Havok specific meshes that are unusable in other environments like OpenSim.

Creating an own physics shape (with shapes being convex if possible) is recommended. Blender has a convex hull function (press space in Edit mode and type it). The smallest possible useful physics shape would therefor be one convex hull shape per object that is decimated to 4 triangles (smallest possible manifold object). Having a good physics shape solves lots of random weird upload failures.

Worn rigged mesh is displayed differently by viewers than unrigged mesh. The Low and Lowest LOD levels of rigged mesh never gets shown, so those can be 0 without problems.
