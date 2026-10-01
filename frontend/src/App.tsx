import { Route, Routes } from "react-router-dom";
import { CustomCursor } from "./components/cursor/CustomCursor";
import { Landing } from "./pages/Landing";
import { Workspace } from "./pages/Workspace";

function App() {
  return (
    <>
      <CustomCursor />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<Workspace />} />
      </Routes>
    </>
  );
}

export default App;
