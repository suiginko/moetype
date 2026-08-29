# moetype

基于萌娘百科词条的输入法词库

词条来源于 [mw2fcitx](https://github.com/outloudvi/mw2fcitx) 以及手动添加，用于便利地输入动漫角色名和声优名等词汇。

<img width="424" height="212" alt="image" src="https://github.com/user-attachments/assets/84c59dd3-fe2f-41bb-81ac-57998a51da90" />

## 如何使用

在 Release 中按需下载适合的版本，将其挂载到一个 Rime 输入方案里（仓库现在只保留“带声调-无辅助码”版本，词库发布主要以 release 为主）

### 下载

- **直接下载**：在仓库的 [Releases (发行版)](../../releases) 中下载对应版本的 `*_moe.dict.yaml`

<details>
<summary><b>使用 Scoop 下载与更新（点击展开）</b></summary>

如果您熟悉命令行操作，推荐使用 [Scoop](https://scoop.sh/) 进行下载和更新（请确保已安装小狼毫作为前端）：

1. 添加 bucket ([Github](https://github.com/abgox/abyss) 或 [Gitee](https://gitee.com/abgox/abyss))：

   - GitHub 源：

     ```shell
     scoop bucket add abyss https://github.com/abgox/abyss
     ```

   - Gitee 镜像：

     ```shell
     scoop bucket add abyss https://gitee.com/abgox/abyss
     ```

2. 按需下载对应版本：

   - **无声调版**

     ```shell
     scoop install abyss/suiginko.moetype.toneless
     ```

   - **有声调版**

     ```shell
     scoop install abyss/suiginko.moetype.tone
     ```

   - **自然码辅助码版**

     ```shell
     scoop install abyss/suiginko.moetype.zrm
     ```

   - **墨奇辅助码版**

     ```shell
     scoop install abyss/suiginko.moetype.moqi
     ```

   - **小鹤辅助码版**

     ```shell
     scoop install abyss/suiginko.moetype.flypy
     ```

> 💡 _注：如果使用 Scoop 下载，请使用下方的「方法 A」进行挂载。_

</details>

> 💡 如果使用的辅助码不在发布列表中，也可以运行仓库中的 `一键生成辅助码版词库脚本.py` 生成任意辅助码的自用版本。

---

### 挂载 (以万象方案为例)

下载完成后，可以通过 `wanxiang.custom.yaml` 将词库加入方案。

<details open>
<summary><b>方法 A：通过 Packs 扩展（推荐）</b></summary>

这种方式不需要修改主词库文件，词库可以单独维护，后续更新更方便。

> ⚠️ **前置注意**：词库文件需直接放在用户目录下，不能放在 `dicts` 子文件夹中。

1. 确保新词库文件命名（例如 `moqi_moe.dict.yaml`）与内部表头的 `name` 保持一致：

   ```yaml
   # Rime dictionary
   ---
   name: moqi_moe
   version: "LTS"
   sort: by_weight
   ...
   ```

2. 在 `wanxiang.custom.yaml` 中追加：

   ```yaml
   patch:
     translator/packs/+:
       - moqi_moe # 填写词库名称，无需带 .dict.yaml
   ```

3. 重新部署即可生效。

</details>

<details>
<summary><b>方法 B：自定义主词库（适合有深度定制需求的用户）</b></summary>

如果需要直接维护一套自己的完整主词库：

1. 复制根目录中的 `wanxiang.dict.yaml`，重命名为 `wanxianguser.dict.yaml`。
2. 将词库内部的 `name` 等信息修改为对应名称（如 `wanxianguser`）。
3. 在 `wanxiang.custom.yaml` 中通过 Patch 统一重定向：

   ```yaml
   patch:
     translator/dictionary: wanxianguser
     user_dict_set/dictionary: wanxianguser
     add_user_dict/dictionary: wanxianguser
   ```

4. 重新部署即可生效。

</details>

---

## 协助修订

如果有修正和添加词条的建议，欢迎：

- 提交 [Issues](../../issues) 或 [Discussions](../../discussions)
- 填写 [在线表格](https://docs.qq.com/smartsheet/DQ29GemR6Z2JJeUd4?tab=t00i2h&viewId=v2JKhc)
- 加入 QQ 群：`781639677`
