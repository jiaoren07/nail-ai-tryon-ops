import { Button, Space, message } from "antd";
import { useUser } from "../store/UserContext";
import api from "../api/client";

export default function DebugBar() {
  const u = useUser();

  const probeBadApi = async () => {
    try {
      await api.get("/api/_does_not_exist");
    } catch {
      // interceptor already shows message.error; swallow here
    }
  };

  const showUserId = () => {
    message.info(`userId = ${u.userId}`);
  };

  return (
    <section className="rounded border border-yellow-300 bg-yellow-50 p-3 text-sm">
      <div className="font-semibold mb-2">Step 5.1 debug bar</div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1 mb-3">
        <div>
          <span className="text-gray-500">userId: </span>
          <code className="text-xs">{u.userId}</code>
        </div>
        <div>
          <span className="text-gray-500">userGender: </span>
          <code className="text-xs">{u.userGender ?? "(null)"}</code>
        </div>
        <div>
          <span className="text-gray-500">photoId: </span>
          <code className="text-xs">{u.photoId ?? "(null)"}</code>
        </div>
        <div>
          <span className="text-gray-500">compareSelection: </span>
          <code className="text-xs">[{u.compareSelection.join(", ")}]</code>
        </div>
      </div>
      <Space wrap size="small">
        <Button size="small" onClick={() => u.setUserGender("female")}>
          set female
        </Button>
        <Button size="small" onClick={() => u.setUserGender("male")}>
          set male
        </Button>
        <Button size="small" onClick={showUserId}>
          show userId
        </Button>
        <Button size="small" onClick={probeBadApi} danger>
          probe bad API
        </Button>
        <Button size="small" onClick={u.resetEverything}>
          reset sessionStorage
        </Button>
      </Space>
    </section>
  );
}
