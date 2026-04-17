// vite.config.ts
import { defineConfig } from "file:///F:/pick/AI%E9%A1%B9%E7%9B%AE/CodeBuddy/WifiEsl/frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///F:/pick/AI%E9%A1%B9%E7%9B%AE/CodeBuddy/WifiEsl/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import UnoCSS from "file:///F:/pick/AI%E9%A1%B9%E7%9B%AE/CodeBuddy/WifiEsl/frontend/node_modules/unocss/dist/vite.mjs";
import { resolve } from "path";
var __vite_injected_original_dirname = "F:\\pick\\AI\u9879\u76EE\\CodeBuddy\\WifiEsl\\frontend";
var vite_config_default = defineConfig({
  plugins: [
    vue(),
    UnoCSS()
  ],
  resolve: {
    alias: {
      "@": resolve(__vite_injected_original_dirname, "src")
    }
  },
  define: {
    __APP_VERSION__: JSON.stringify("1.1.1"),
    __BUILD_TIME__: JSON.stringify((/* @__PURE__ */ new Date()).toLocaleString("zh-CN", { hour12: false }))
  },
  server: {
    host: "0.0.0.0",
    // 监听所有网卡，支持局域网访问
    port: 3e3,
    open: true,
    proxy: {
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true
      },
      "/ws": {
        target: "ws://localhost:8001",
        ws: true
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: "modern-compiler",
        additionalData: `@use "@/assets/styles/variables" as *;`
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJGOlxcXFxwaWNrXFxcXEFJXHU5ODc5XHU3NkVFXFxcXENvZGVCdWRkeVxcXFxXaWZpRXNsXFxcXGZyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJGOlxcXFxwaWNrXFxcXEFJXHU5ODc5XHU3NkVFXFxcXENvZGVCdWRkeVxcXFxXaWZpRXNsXFxcXGZyb250ZW5kXFxcXHZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9GOi9waWNrL0FJJUU5JUExJUI5JUU3JTlCJUFFL0NvZGVCdWRkeS9XaWZpRXNsL2Zyb250ZW5kL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcclxuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXHJcbmltcG9ydCBVbm9DU1MgZnJvbSAndW5vY3NzL3ZpdGUnXHJcbmltcG9ydCB7IHJlc29sdmUgfSBmcm9tICdwYXRoJ1xyXG5cclxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcclxuICBwbHVnaW5zOiBbXHJcbiAgICB2dWUoKSxcclxuICAgIFVub0NTUygpLFxyXG4gIF0sXHJcbiAgcmVzb2x2ZToge1xyXG4gICAgYWxpYXM6IHtcclxuICAgICAgJ0AnOiByZXNvbHZlKF9fZGlybmFtZSwgJ3NyYycpLFxyXG4gICAgfSxcclxuICB9LFxyXG4gIGRlZmluZToge1xyXG4gICAgX19BUFBfVkVSU0lPTl9fOiBKU09OLnN0cmluZ2lmeSgnMS4xLjEnKSxcclxuICAgIF9fQlVJTERfVElNRV9fOiBKU09OLnN0cmluZ2lmeShuZXcgRGF0ZSgpLnRvTG9jYWxlU3RyaW5nKCd6aC1DTicsIHsgaG91cjEyOiBmYWxzZSB9KSksXHJcbiAgfSxcclxuICBzZXJ2ZXI6IHtcclxuICAgIGhvc3Q6ICcwLjAuMC4wJywgICAvLyBcdTc2RDFcdTU0MkNcdTYyNDBcdTY3MDlcdTdGNTFcdTUzNjFcdUZGMENcdTY1MkZcdTYzMDFcdTVDNDBcdTU3REZcdTdGNTFcdThCQkZcdTk1RUVcclxuICAgIHBvcnQ6IDMwMDAsXHJcbiAgICBvcGVuOiB0cnVlLFxyXG4gICAgcHJveHk6IHtcclxuICAgICAgJy9hcGknOiB7XHJcbiAgICAgICAgdGFyZ2V0OiAnaHR0cDovL2xvY2FsaG9zdDo4MDAxJyxcclxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWUsXHJcbiAgICAgIH0sXHJcbiAgICAgICcvd3MnOiB7XHJcbiAgICAgICAgdGFyZ2V0OiAnd3M6Ly9sb2NhbGhvc3Q6ODAwMScsXHJcbiAgICAgICAgd3M6IHRydWUsXHJcbiAgICAgIH0sXHJcbiAgICB9LFxyXG4gIH0sXHJcbiAgY3NzOiB7XHJcbiAgICBwcmVwcm9jZXNzb3JPcHRpb25zOiB7XHJcbiAgICAgIHNjc3M6IHtcclxuICAgICAgICBhcGk6ICdtb2Rlcm4tY29tcGlsZXInLFxyXG4gICAgICAgIGFkZGl0aW9uYWxEYXRhOiBgQHVzZSBcIkAvYXNzZXRzL3N0eWxlcy92YXJpYWJsZXNcIiBhcyAqO2AsXHJcbiAgICAgIH0sXHJcbiAgICB9LFxyXG4gIH0sXHJcbn0pXHJcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBbVUsU0FBUyxvQkFBb0I7QUFDaFcsT0FBTyxTQUFTO0FBQ2hCLE9BQU8sWUFBWTtBQUNuQixTQUFTLGVBQWU7QUFIeEIsSUFBTSxtQ0FBbUM7QUFLekMsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDMUIsU0FBUztBQUFBLElBQ1AsSUFBSTtBQUFBLElBQ0osT0FBTztBQUFBLEVBQ1Q7QUFBQSxFQUNBLFNBQVM7QUFBQSxJQUNQLE9BQU87QUFBQSxNQUNMLEtBQUssUUFBUSxrQ0FBVyxLQUFLO0FBQUEsSUFDL0I7QUFBQSxFQUNGO0FBQUEsRUFDQSxRQUFRO0FBQUEsSUFDTixpQkFBaUIsS0FBSyxVQUFVLE9BQU87QUFBQSxJQUN2QyxnQkFBZ0IsS0FBSyxXQUFVLG9CQUFJLEtBQUssR0FBRSxlQUFlLFNBQVMsRUFBRSxRQUFRLE1BQU0sQ0FBQyxDQUFDO0FBQUEsRUFDdEY7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sT0FBTztBQUFBLE1BQ0wsUUFBUTtBQUFBLFFBQ04sUUFBUTtBQUFBLFFBQ1IsY0FBYztBQUFBLE1BQ2hCO0FBQUEsTUFDQSxPQUFPO0FBQUEsUUFDTCxRQUFRO0FBQUEsUUFDUixJQUFJO0FBQUEsTUFDTjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQUEsRUFDQSxLQUFLO0FBQUEsSUFDSCxxQkFBcUI7QUFBQSxNQUNuQixNQUFNO0FBQUEsUUFDSixLQUFLO0FBQUEsUUFDTCxnQkFBZ0I7QUFBQSxNQUNsQjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
