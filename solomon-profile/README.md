# solomon-profile — Solomon 정체성 소스 (버전관리)

Solomon(AI CEO)의 **정체성·사용자 프로필의 버전관리 소스**다(시크릿 아님). 컨테이너 데이터 홈(`hermes-home/`, `/opt/data`)에 배포해 사용한다.

- `SOUL.md` — Solomon의 정체성·역할 경계·운영 원칙·승인 게이트
- `USER.md` — Sam(창업자) 프로필/선호

## 배포 방법 (초기 설정 후)
`docker compose run --rm hermes-solomon setup` 으로 기본 설정을 마친 뒤:

- **기본 프로필로 쓸 경우**: 이 파일들을 데이터 홈 루트에 복사
  ```bash
  cp solomon-profile/SOUL.md hermes-home/SOUL.md
  mkdir -p hermes-home/memories && cp solomon-profile/USER.md hermes-home/memories/USER.md
  ```
- **named 프로필 `solomon`으로 쓸 경우**: 프로필 생성 후 해당 경로에 복사
  ```bash
  docker compose run --rm hermes-solomon profile create solomon
  cp solomon-profile/SOUL.md hermes-home/profiles/solomon/SOUL.md
  mkdir -p hermes-home/profiles/solomon/memories && cp solomon-profile/USER.md hermes-home/profiles/solomon/memories/USER.md
  ```

> 상세 절차는 [`../docs/05_stage0_setup_guide.md`](../docs/05_stage0_setup_guide.md) 참고.
