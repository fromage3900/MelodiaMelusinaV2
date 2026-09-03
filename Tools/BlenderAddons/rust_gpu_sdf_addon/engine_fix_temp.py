        import time
        t_start = time.perf_counter()
        
        mesh = output_obj.data
        mesh.clear_geometry()
        
        # 面データの生成 (foreach_set による高速化)
        try:
            v_count = len(verts_np)
            f_count = len(indices_np) // 3
            
            mesh.vertices.add(v_count)
            mesh.vertices.foreach_set("co", verts_np[:, 0:3].ravel())
            
            mesh.loops.add(len(indices_np))
            mesh.loops.foreach_set("vertex_index", indices_np)
            
            mesh.polygons.add(f_count)
            mesh.polygons.foreach_set("loop_start", np.arange(0, len(indices_np), 3, dtype=np.int32))
            mesh.polygons.foreach_set("loop_total", np.full(f_count, 3, dtype=np.int32))
            
        except Exception as pydata_err:
            print(f"SDF Mesh creation error (fast path): {pydata_err}")
            return

        if "Color" not in mesh.attributes:
            mesh.attributes.new(name="Color", type='FLOAT_COLOR', domain='POINT')
        mesh.attributes["Color"].data.foreach_set("color", colors_rgba)

        if "Metallic" not in mesh.attributes:
            mesh.attributes.new(name="Metallic", type='FLOAT', domain='POINT')
        mesh.attributes["Metallic"].data.foreach_set("value", metallic_data)

        if "Roughness" not in mesh.attributes:
            mesh.attributes.new(name="Roughness", type='FLOAT', domain='POINT')
        mesh.attributes["Roughness"].data.foreach_set("value", roughness_data)
        
        # スムーズシェーディングの設定
        if mesh.polygons:
            mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))

        # カスタム法線の適用 (必要な場合のみ)
        if mesh.loops and (output_obj.sdf_props.use_live_normals or force_normals):
            try:
                v_indices = np.empty(len(mesh.loops), dtype=np.int32)
                mesh.loops.foreach_get("vertex_index", v_indices)
                normals_flat = verts_np[:, 8:11].astype(np.float32)
                normals_flat = np.nan_to_num(normals_flat)
                v_indices = np.clip(v_indices, 0, len(normals_flat) - 1)
                final_loop_normals = normals_flat[v_indices]
                mesh.normals_split_custom_set(final_loop_normals)
                if hasattr(mesh, "use_auto_smooth"):
                    mesh.use_auto_smooth = True
            except Exception as normal_err:
                print(f"SDF Normal Apply Warning: {normal_err}")
        elif mesh.loops and not output_obj.sdf_props.use_live_normals:
            if hasattr(mesh, "normals_split_custom_clear"):
                mesh.normals_split_custom_clear()
            
        # 最後に一度だけ更新
        mesh.update()
        
        # 適用時間のログ (デバッグ用)
        # print(f"SDF Debug: Mesh Applied in {(time.perf_counter() - t_start)*1000:.2f} ms")
        
    except Exception as e:
        print(f"SDF Apply Error: {e}")
